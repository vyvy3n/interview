"""Mock 9 — Tokenizer (BM25 retrieval pipeline). REFERENCE SOLUTION.

This is the clean reference. `tokenize_lib.py` is this file with a bug planted.
"""


def tokenize(text: str) -> list[str]:
    """Lowercase the text, split on whitespace, drop empty tokens.

    Empty tokens come from runs of whitespace at the edges or between words —
    they're not real terms and must not enter the index.
    """
    return [t for t in text.lower().split() if t]
