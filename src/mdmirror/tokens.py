from __future__ import annotations

# tiktoken's o200k_base encoding (GPT-4o) — within ~5% of Claude's tokenizer
# for typical English/code; close enough for "does this fit in 200K context".
# Anthropic does not ship a public local tokenizer.
_ENCODING_NAME = "o200k_base"
_encoding = None


def count_tokens(text: str) -> int:
    """Return the exact token count for `text` under the o200k_base encoding."""
    if not text:
        return 0
    enc = _get_encoding()
    return len(enc.encode(text))


def _get_encoding():
    global _encoding
    if _encoding is None:
        import tiktoken

        _encoding = tiktoken.get_encoding(_ENCODING_NAME)
    return _encoding
