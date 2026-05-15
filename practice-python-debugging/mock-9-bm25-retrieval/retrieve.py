"""Mock 9 — Retrieval pipeline (BM25 retrieval pipeline). [HARD — MULTI-MODULE]

Tie tokenize + index + scorer together to actually answer a query.

  top_k(scored, k)
      Sort the {doc_id: score} dict by descending score (ties broken by
      doc_id ascending for determinism), wrap the survivors in
      QueryResult NamedTuples, return the first k. Fewer than k scored
      docs returns all of them — no padding.

  query(index, q, k)
      Tokenize the query string, score every doc that contains at least
      one query term, return the top k. A doc's score is the SUM of its
      per-query-term contributions, so this function must ACCUMULATE
      (+=) across query terms — overwriting (=) loses every contribution
      except the last term's. Query terms not in the index are silently
      SKIPPED — they don't crash and don't contribute.

  parse_query(tokens)
      Parse a flat boolean query (alternating term / AND-or-OR / term)
      into ('AND', [terms]) or ('OR', [terms]). Recursive: peel the head
      term, decide the connective from the operator after it, recurse on
      the tail. The recursive call's term list must be PREPENDED with
      the head term — discarding the recursive result is the classic bug.

---
This module has bugs. The unittest suite in `test_pipeline.py` is the
spec for the WHOLE pipeline. Do not edit the test file or the
`*_solution.py` reference files.
"""
from typing import NamedTuple

from tokenize_lib import tokenize
from inverted_index import InvertedIndex
from bm25 import idf, tf_saturation, score_term


class QueryResult(NamedTuple):
    doc_id: str
    score: float


def top_k(scored: dict[str, float], k: int) -> list[QueryResult]:
    """Return the top k (doc_id, score) pairs by descending score; ties
    broken by doc_id ascending. If fewer than k docs have scores, return
    all of them (not padded).
    """
    items = list(scored.items())
    items.sort(key=lambda dx: (dx[1], dx[0]))
    return [d for d, s in items[:k]]


def query(index: InvertedIndex, q: str, k: int = 10) -> list[QueryResult]:
    """Tokenize the query, score every doc that contains at least one query
    term, return the top-k.
    """
    terms = tokenize(q)
    avgdl = index.avg_doc_length()
    scored: dict[str, float] = {}
    for term in terms:
        df = index._doc_freq[term]
        if df == 0:
            continue
        term_idf = idf(index.num_docs, df)
        for entry in index._postings[term]:
            tf_sat = tf_saturation(entry.term_freq, entry.doc_length, avgdl)
            scored[entry.doc_id] = score_term(term_idf, tf_sat)
    return top_k(scored, k)


def parse_query(tokens: list[str]) -> tuple:
    """Parse a flat boolean query into ('AND', [terms]) or ('OR', [terms]).

    The token list alternates: term, OP, term, OP, term, ...  A single
    bare term parses as ('AND', [term]); the empty query parses as
    ('AND', []).
    """
    if not tokens:
        return ("AND", [])
    if len(tokens) == 1:
        return ("AND", [tokens[0]])
    op = tokens[1]
    if op not in ("AND", "OR"):
        return ("AND", list(tokens))
    _, rest_terms = parse_query(tokens[2:])
    return (op, [tokens[0]])
