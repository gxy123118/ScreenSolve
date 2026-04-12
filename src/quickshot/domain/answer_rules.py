from __future__ import annotations

import json
import re
from typing import Any

NO_ANSWER = "未识别到可用答案"

OCR_REASON_SYSTEM_PROMPT = """
你是选择题文本判题器。
输入是 OCR 识别出来的原始文本，可能有少量错字、空格错误和换行错误。

你需要只输出最终答案，不要解释，不要分析，不要输出 Markdown 或 <think>。
优先输出 JSON，格式固定为：
{"answers":[{"question_no":"11","choice":"B","answer_text":"被选中选项的完整原文"}]}

规则：
1. 只回答 OCR 文本中清晰可见的题目。
2. question_no 必须与 OCR 文本中的题号一致，禁止重编号。
3. choice 只能是 A/B/C/D。
4. answer_text 必须尽量复制对应选项原文。
5. 如果无法 100% 确定，也返回最可能正确的选项，不要留空。
6. JSON 必须可解析。
""".strip()

OCR_REASON_FALLBACK_PROMPT = """
你是选择题文本判题器。
输入是 OCR 原始文本。只输出最终答案，不要解释。

每行格式固定为：题号.选项:答案原文
例如：11.B:二叉树的中序遍历结果

规则：
1. 题号必须与 OCR 文本一致。
2. 不要输出额外说明。
3. 如果无法完全确定，也给出最可能正确的答案。
""".strip()


def sanitize_model_output(text: str) -> str:
    cleaned = text or ""
    cleaned = re.sub(r"```(?:json|JSON)?", "", cleaned)
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"<think>[\s\S]*?(</think>|$)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"<analysis>[\s\S]*?(</analysis>|$)", "", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"</?think>|</?analysis>", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def normalize_answer(text: str, extracted_json: str = "") -> str:
    cleaned = sanitize_model_output(text)
    if not cleaned:
        return NO_ANSWER

    options_by_qid = _load_options_map(extracted_json)

    json_answer = _normalize_json_answer(cleaned, options_by_qid)
    if json_answer:
        return json_answer

    text_answer = _normalize_text_answer(cleaned, options_by_qid)
    if text_answer:
        return text_answer

    single_question_answer = _normalize_single_question_reasoning(
        cleaned, options_by_qid
    )
    if single_question_answer:
        return single_question_answer

    return NO_ANSWER


def compact_ocr_text(text: str) -> str:
    text = text or ""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _load_options_map(extracted_json: str) -> dict[str, dict[str, str]]:
    if not extracted_json.strip():
        return {}

    try:
        payload = json.loads(extracted_json)
    except json.JSONDecodeError:
        return {}

    questions = payload.get("questions", [])
    if not isinstance(questions, list):
        return {}

    mapped: dict[str, dict[str, str]] = {}
    for question in questions:
        if not isinstance(question, dict):
            continue
        qid = str(question.get("question_no", "")).strip()
        if not qid:
            continue
        options = question.get("options", {})
        if not isinstance(options, dict):
            continue
        normalized_options: dict[str, str] = {}
        for key, value in options.items():
            choice = str(key).strip().upper()
            if not re.fullmatch(r"[A-Z0-9]", choice):
                continue
            normalized_options[choice] = str(value).strip()
        mapped[qid] = normalized_options
    return mapped


def _normalize_json_answer(
    cleaned: str, options_by_qid: dict[str, dict[str, str]]
) -> str:
    for candidate in _candidate_json_blocks(cleaned):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        answers = _extract_answers(payload)
        normalized = _format_answers(answers, options_by_qid)
        if normalized:
            return normalized
    return ""


def _candidate_json_blocks(text: str) -> list[str]:
    candidates: list[str] = []
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        candidates.append(stripped)

    for match in re.finditer(r"\{[\s\S]*?\}", text):
        candidates.append(match.group(0))

    seen: set[str] = set()
    ordered: list[str] = []
    for item in candidates:
        if item in seen:
            continue
        ordered.append(item)
        seen.add(item)
    return ordered


def _extract_answers(payload: Any) -> list[dict[str, str]]:
    if isinstance(payload, dict):
        raw_answers = payload.get("answers", payload.get("results", []))
    elif isinstance(payload, list):
        raw_answers = payload
    else:
        return []

    if not isinstance(raw_answers, list):
        return []

    answers: list[dict[str, str]] = []
    for item in raw_answers:
        if not isinstance(item, dict):
            continue
        qid = str(item.get("question_no", item.get("id", ""))).strip()
        choice = str(item.get("choice", item.get("option", ""))).strip().upper()
        answer_text = str(item.get("answer_text", item.get("text", ""))).strip()
        answers.append(
            {
                "question_no": qid,
                "choice": choice,
                "answer_text": answer_text,
            }
        )
    return answers


def _format_answers(
    answers: list[dict[str, str]], options_by_qid: dict[str, dict[str, str]]
) -> str:
    lines: list[str] = []
    seen: set[str] = set()

    for item in answers:
        qid = item.get("question_no", "").strip()
        choice = item.get("choice", "").strip().upper()
        answer_text = item.get("answer_text", "").strip()

        if not qid.isdigit() or not re.fullmatch(r"[A-Z0-9]", choice):
            continue
        if qid in seen:
            continue

        if not answer_text:
            answer_text = options_by_qid.get(qid, {}).get(choice, "")
        if not answer_text:
            answer_text = f"选{choice}"

        lines.append(f"{qid}.{choice}:{answer_text}")
        seen.add(qid)

    return "\n".join(lines)


def _normalize_text_answer(
    cleaned: str, options_by_qid: dict[str, dict[str, str]]
) -> str:
    answers: list[dict[str, str]] = []

    for qid, choice, answer_text in re.findall(
        r"\b(\d+)\s*[.)、]\s*([A-Za-z0-9])\s*[:：]\s*([^\n]+)", cleaned
    ):
        answers.append(
            {
                "question_no": qid.strip(),
                "choice": choice.strip().upper(),
                "answer_text": answer_text.strip(),
            }
        )

    if not answers:
        for qid, choice in re.findall(r"\b(\d+)\s*[.)、]\s*([A-Za-z0-9])\b", cleaned):
            answers.append(
                {
                    "question_no": qid.strip(),
                    "choice": choice.strip().upper(),
                    "answer_text": "",
                }
            )

    if not answers:
        for qid, choice in re.findall(
            r"第?\s*(\d+)\s*题[^\n]{0,16}?(?:答案是|选)\s*([A-Za-z0-9])",
            cleaned,
        ):
            answers.append(
                {
                    "question_no": qid.strip(),
                    "choice": choice.strip().upper(),
                    "answer_text": "",
                }
            )

    return _format_answers(answers, options_by_qid)


def _normalize_single_question_reasoning(
    cleaned: str, options_by_qid: dict[str, dict[str, str]]
) -> str:
    if len(options_by_qid) != 1:
        return ""

    qid = next(iter(options_by_qid))
    patterns = [
        r"(?:正确答案|答案|最终答案)[^\n]{0,8}?(?:是|为|选)\s*([A-Za-z0-9])",
        r"(?:correct answer|final answer)[^\n]{0,8}?(?:is|:)\s*([A-Za-z0-9])",
        r"\b([A-Za-z0-9])\s+is\s+correct\b",
        r"(?:option|choice)\s*([A-Za-z0-9])\s*(?:is correct|is the correct answer)",
        r"(?:\*\*)?(?:选项|option)\s*([A-Za-z0-9])(?:\*\*)?\s*[:：][\s\S]{0,300}?(?:这是正确的|是正确的|is correct)",
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if not match:
            continue

        choice = match.group(1).strip().upper()
        return _format_answers(
            [{"question_no": qid, "choice": choice, "answer_text": ""}],
            options_by_qid,
        )
    return ""
