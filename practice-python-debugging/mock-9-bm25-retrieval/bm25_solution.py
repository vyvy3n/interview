"""Mock 9 — BM25 scoring (BM25 retrieval pipeline). REFERENCE SOLUTION.

This is the clean reference. `bm25.py` is this file with bugs planted.
"""
import numpy as np


def idf(num_docs: int, doc_freq: int) -> float:
    """Smoothed IDF: log((N - df + 0.5) / (df + 0.5) + 1).

    The +0.5 smoothing and the +1 inside the log mean this is:
      - finite even when df=0 (unseen term) — no ZeroDivisionError;
      - non-negative for every df in [0, N] — even a term in every doc
        gets a small positive weight, not a negative one.
    """
    return float(np.log((num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1))


def tf_saturation(
    tf: int,
    doc_length: int,
    avg_doc_length: float,
    k1: float = 1.2,
    b: float = 0.75,
) -> float:
    """Saturating TF with length normalization:

        tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))

    Grows monotonically with `tf` and asymptotes near `(k1 + 1)`. Documents
    longer than average are penalized; shorter than average are boosted.
    Returns 0.0 when avg_doc_length is 0 (empty corpus — nothing to score).
    """
    if avg_doc_length == 0:
        return 0.0
    length_norm = 1 - b + b * (doc_length / avg_doc_length)
    return (tf * (k1 + 1)) / (tf + k1 * length_norm)


def score_term(term_idf: float, term_tf_sat: float) -> float:
    """One term's BM25 contribution to a doc's score: idf * tf_saturation.

    Both factors are non-negative, so the product is too. A term with zero
    idf or zero saturation contributes nothing.
    """
    return term_idf * term_tf_sat
