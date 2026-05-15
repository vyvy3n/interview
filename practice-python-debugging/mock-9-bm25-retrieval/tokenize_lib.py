"""Mock 9 — Tokenizer (BM25 retrieval pipeline). [HARD — MULTI-MODULE]

Tokenize text into lowercase word tokens for the BM25 retrieval pipeline.

The pipeline's input is raw user text — strings copied from documents,
typed into a search box — so the tokenizer is the funnel everything else
passes through. A bug here propagates: weird tokens end up as phantom
terms in the inverted index, which corrupt idf, which corrupt every
BM25 score, which corrupt every ranking. When you see a downstream
oddity, suspect the tokenizer too.

---
This module has a bug. The unittest suite in `test_pipeline.py` is the
spec for the WHOLE pipeline — fix the root cause of every failure (across
ALL four modules) so the suite passes. Do not edit the test file or the
`*_solution.py` reference files.
"""


def tokenize(text: str) -> list[str]:
    """Lowercase the text, split on whitespace, drop empty tokens.

    Empty tokens come from runs of whitespace (leading, trailing, or
    between words) — they must not enter the index as phantom terms.
    """
    return [t for t in text.lower().split(" ")]
