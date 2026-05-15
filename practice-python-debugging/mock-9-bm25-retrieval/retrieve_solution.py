"""Mock 9 — Retrieval pipeline (BM25 retrieval pipeline). REFERENCE SOLUTION.

This is the clean reference. `retrieve.py` is this file with bugs planted.
"""
from typing import NamedTuple

from tokenize_lib_solution import tokenize
from inverted_index_solution import InvertedIndex
from bm25_solution import idf, tf_saturation, score_term


class QueryResult(NamedTuple):
    doc_id: str
    score: float


def top_k(scored: dict[str, float], k: int) -> list[QueryResult]:
    """Return the top k (doc_id, score) pairs by descending score; ties
    broken by doc_id ascending. If fewer than k docs have scores, return
    all of them (not padded).
    """
    items = list(scored.items())
    items.sort(key=lambda dx: (-dx[1], dx[0]))
    return [QueryResult(doc_id=d, score=s) for d, s in items[:k]]


def query(index: InvertedIndex, q: str, k: int = 10) -> list[QueryResult]:
    """Tokenize the query, score every doc that contains at least one query
    term, return the top-k.

    Query terms not in the index are SKIPPED — they contribute nothing.
    A doc's score is the SUM of its per-term contributions, so we must
    accumulate (+=) across query terms, not overwrite (=).
    """
    terms = tokenize(q)
    avgdl = index.avg_doc_length()
    scored: dict[str, float] = {}
    for term in terms:
        df = index.doc_freq(term)
        if df == 0:
            continue
        term_idf = idf(index.num_docs, df)
        for entry in index.postings(term):
            tf_sat = tf_saturation(entry.term_freq, entry.doc_length, avgdl)
            scored[entry.doc_id] = scored.get(entry.doc_id, 0.0) + score_term(term_idf, tf_sat)
    return top_k(scored, k)


def parse_query(tokens: list[str]) -> tuple:
    """Parse a flat boolean query into ('AND', [terms]) or ('OR', [terms]).

    The token list alternates: term, OP, term, OP, term, ...  All operators
    in one query must be the same (no mixed AND/OR). A single bare term
    parses as ('AND', [term]); the empty query parses as ('AND', []).

    Recursive structure: peel the head term off, decide the connective
    from token[1] (an operator), then recurse on the tail starting at
    token[2]. The recursive call returns the operator and the rest of the
    terms — PREPEND the head term to that list and return. Discarding the
    recursive call's term list is the classic bug.
    """
    if not tokens:
        return ("AND", [])
    if len(tokens) == 1:
        return ("AND", [tokens[0]])
    # tokens[1] is the operator that joins tokens[0] with everything after.
    op = tokens[1]
    if op not in ("AND", "OR"):
        # No operator between tokens — implicit AND of all of them.
        return ("AND", list(tokens))
    _, rest_terms = parse_query(tokens[2:])
    return (op, [tokens[0]] + rest_terms)
