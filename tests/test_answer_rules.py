from quickshot.domain.answer_rules import NO_ANSWER, compact_ocr_text, normalize_answer


EXTRACTED_JSON = (
    '{"questions":[{"question_no":"2","stem":"以下关于死锁的描述中，哪一项是正确的？",'
    '"options":{"A":"死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。",'
    '"B":"死锁可以通过增加资源数量来完全避免。",'
    '"C":"死锁预防是通过检测和恢复机制来解决死锁问题。",'
    '"D":"死锁避免算法（如银行家算法）只能在死锁发生后进行处理。"}}]}'
)


def test_normalize_answer_keeps_question_numbers() -> None:
    text = "11.B:foo\n12.C:bar"
    assert normalize_answer(text) == "11.B:foo\n12.C:bar"


def test_normalize_answer_supports_simple_form_and_fills_option_text() -> None:
    text = "2.A"
    assert normalize_answer(text, EXTRACTED_JSON) == (
        "2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
    )


def test_normalize_answer_supports_json_payload() -> None:
    text = (
        '{"answers":[{"question_no":"2","choice":"A",'
        '"answer_text":"死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"}]}'
    )
    assert normalize_answer(text, EXTRACTED_JSON) == (
        "2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
    )


def test_normalize_answer_supports_prose_form() -> None:
    text = "第2题答案是A"
    assert normalize_answer(text, EXTRACTED_JSON) == (
        "2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
    )


def test_normalize_answer_drops_think() -> None:
    text = "<think>ignore</think>\n2.A"
    assert normalize_answer(text, EXTRACTED_JSON) == (
        "2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
    )


def test_normalize_answer_supports_single_question_reasoning_fallback() -> None:
    text = "让我分析这道题。\n因此，正确答案是A"
    assert normalize_answer(text, EXTRACTED_JSON) == (
        "2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
    )


def test_normalize_answer_supports_single_question_english_reasoning() -> None:
    text = "Analysis: A is correct because it lists the four necessary conditions."
    assert normalize_answer(text, EXTRACTED_JSON) == (
        "2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
    )


def test_normalize_answer_supports_option_correct_reasoning() -> None:
    text = (
        "选项A：死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
        "这是正确的。"
    )
    assert normalize_answer(text, EXTRACTED_JSON) == (
        "2.A:死锁的四个必要条件分别是：互斥条件、占有并等待、非抢占条件和循环等待条件。"
    )


def test_normalize_answer_empty() -> None:
    assert normalize_answer("   ") == NO_ANSWER


def test_compact_ocr_text() -> None:
    raw = "2.  死锁题\r\n\r\nA.  选项A   \r\nB.  选项B"
    assert compact_ocr_text(raw) == "2. 死锁题\n\nA. 选项A \nB. 选项B"
