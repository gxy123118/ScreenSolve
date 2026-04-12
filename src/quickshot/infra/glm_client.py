from __future__ import annotations

import os
import time

import requests

from quickshot.domain.answer_rules import (
    NO_ANSWER,
    OCR_REASON_FALLBACK_PROMPT,
    OCR_REASON_SYSTEM_PROMPT,
    compact_ocr_text,
    normalize_answer,
)


class RateLimitError(RuntimeError):
    pass


class GLMClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        api_key_env: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key.strip()
        self._api_key_env = api_key_env
        self._session = requests.Session()

    def solve_from_ocr(self, ocr_text: str) -> str:
        api_key = self._api_key or os.environ.get(self._api_key_env, "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing API key. Set ai_api_key in quickshot.toml "
                f"or environment variable {self._api_key_env}"
            )

        compact_text = compact_ocr_text(ocr_text)
        if not compact_text:
            return NO_ANSWER

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        raw = self._solve_text_question(url, headers, compact_text)
        answer = normalize_answer(raw)
        if answer != NO_ANSWER:
            return answer

        fallback_raw = self._solve_text_question_fallback(url, headers, compact_text)
        return normalize_answer(fallback_raw)

    def _solve_text_question(
        self, url: str, headers: dict[str, str], ocr_text: str
    ) -> str:
        payload = {
            "model": self._model,
            "temperature": 0,
            "max_tokens": 240,
            "thinking": {"type": "disabled"},
            "messages": [
                {"role": "system", "content": OCR_REASON_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"以下是截图经过 OCR 提取出的文本，请直接作答：\n\n{ocr_text}",
                },
            ],
        }
        return self._request_with_retry(url, headers, payload)

    def _solve_text_question_fallback(
        self, url: str, headers: dict[str, str], ocr_text: str
    ) -> str:
        payload = {
            "model": self._model,
            "temperature": 0,
            "max_tokens": 200,
            "thinking": {"type": "disabled"},
            "messages": [
                {"role": "system", "content": OCR_REASON_FALLBACK_PROMPT},
                {
                    "role": "user",
                    "content": f"以下是 OCR 文本，只输出最终答案：\n\n{ocr_text}",
                },
            ],
        }
        return self._request_with_retry(url, headers, payload)

    def _request_with_retry(self, url: str, headers: dict[str, str], payload: dict) -> str:
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            resp = self._session.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 401:
                raise RuntimeError(
                    "Unauthorized (401): invalid API key or key has no permission "
                    f"for this endpoint ({url})."
                )
            if resp.status_code == 429:
                retry_after = self._retry_after_seconds(resp)
                if attempt >= max_attempts:
                    raise RateLimitError(
                        f"GLM rate limited (429). Retry after about {retry_after:.1f}s."
                    )
                time.sleep(retry_after)
                continue

            if 500 <= resp.status_code < 600 and attempt < max_attempts:
                time.sleep(0.8 * attempt)
                continue

            resp.raise_for_status()
            data = resp.json()
            return self._extract_content(data)

        raise RuntimeError("GLM request failed after retries.")

    @staticmethod
    def _retry_after_seconds(resp: requests.Response) -> float:
        value = resp.headers.get("Retry-After", "").strip()
        if value:
            try:
                return max(0.5, float(value))
            except ValueError:
                pass
        return 1.2

    @staticmethod
    def _extract_content(data: dict) -> str:
        try:
            message = data["choices"][0]["message"]
        except Exception:
            return str(data)

        content = message.get("content", "")
        reasoning_content = message.get("reasoning_content", "")

        if isinstance(content, str):
            text = content.strip()
            if text:
                return text
            if isinstance(reasoning_content, str) and reasoning_content.strip():
                return reasoning_content.strip()
            return str(message)

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    txt = item.get("text") or item.get("content")
                    if txt:
                        parts.append(str(txt))
            merged = "\n".join(parts).strip()
            if merged:
                return merged
            if isinstance(reasoning_content, str) and reasoning_content.strip():
                return reasoning_content.strip()
            return str(message)

        if isinstance(reasoning_content, str) and reasoning_content.strip():
            return reasoning_content.strip()
        return str(content)
