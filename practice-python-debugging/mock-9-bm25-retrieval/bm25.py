"""Mock 9 — BM25 scoring (BM25 retrieval pipeline). [HARD — MULTI-MODULE]

The three scoring primitives the query pipeline composes.

  idf(N, df)
      How informative a term is. Rare terms (low df) carry a lot of
      signal; terms that show up in every document carry almost none.
      Must be FINITE at df=0 (an unseen term shows up briefly while we
      decide to skip it) and NON-NEGATIVE for every df in [0, N].

  tf_saturation(tf, dl, avgdl, k1, b)
      Per-term contribution per-doc. Grows monotonically with `tf` but
      with diminishing returns (asymptotes near k1+1, by default 2.2),
      and applies length-normalisation so a hit in a 1000-token doc
      counts for less than a hit in a 10-token doc.

  score_term(idf, tfsat)
      The product. Both inputs are non-negative; the result is the
      per-(query-term, doc) BM25 contribution.

---
This module has bugs. The unittest suite in `test_pipeline.py` is the
spec for the WHOLE pipeline. Do not edit the test file or the
`*_solution.py` reference files.
"""
import numpy as np


def idf(num_docs: int, doc_freq: int) -> float:
    """Smoothed IDF — finite at df=0, non-negative at df=N.

    Formula: log((N - df + 0.5) / (df + 0.5) + 1)
    """
    return float(np.log(num_docs / doc_freq))


def tf_saturation(
    tf: int,
    doc_length: int,
    avg_doc_length: float,
    k1: float = 1.2,
    b: float = 0.75,
) -> float:
    """Saturating TF with length normalization:

        tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))

    Grows with tf, asymptotes near (k1 + 1). Long docs penalised.
    """
    if avg_doc_length == 0:
        return 0.0
    length_norm = 1 - b + b * (doc_length / avg_doc_length)
    return tf / (tf + k1 * length_norm)


def score_term(term_idf: float, term_tf_sat: float) -> float:
    """One term's BM25 contribution to a doc's score: idf * tf_saturation."""
    return float(np.where(term_idf > 0, 0.0, term_idf * term_tf_sat))
