from mdmirror.tokens import count_tokens


def test_empty_string_is_zero() -> None:
    assert count_tokens("") == 0


def test_short_text_positive_count() -> None:
    n = count_tokens("hello world")
    assert n > 0
    # "hello world" is 2 tokens under both o200k_base and cl100k_base.
    assert n == 2


def test_caches_encoding(monkeypatch) -> None:
    import mdmirror.tokens as tk

    monkeypatch.setattr(tk, "_encoding", None)
    a = count_tokens("first call")
    encoded_once = tk._encoding
    b = count_tokens("second call")
    assert tk._encoding is encoded_once  # same object reused
    assert a > 0 and b > 0


def test_code_text_has_reasonable_count() -> None:
    code = "def foo(x: int) -> int:\n    return x + 1\n"
    n = count_tokens(code)
    # Sanity: not 0, not absurdly high.
    assert 5 <= n <= 50
