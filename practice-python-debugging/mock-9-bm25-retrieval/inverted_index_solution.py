"""Mock 9 — Inverted index (BM25 retrieval pipeline). REFERENCE SOLUTION.

This is the clean reference. `inverted_index.py` is this file with bugs planted.
"""
from typing import NamedTuple

from tokenize_lib_solution import tokenize


class Document(NamedTuple):
    doc_id: str
    text: str


class IndexEntry(NamedTuple):
    doc_id: str
    term_freq: int
    doc_length: int


class InvertedIndex:
    """term -> postings list, plus per-doc length and corpus average length.

    `add_documents` is the only mutator: every call resets the index and
    rebuilds it from scratch on the new corpus. `prune_rare_terms` drops
    low-doc-frequency terms in place (call it after building).
    """

    def __init__(self):
        self._postings: dict[str, list[IndexEntry]] = {}
        self._doc_freq: dict[str, int] = {}
        self._doc_lengths: dict[str, int] = {}
        self._avg_doc_length: float = 0.0
        self.num_docs: int = 0

    def add_documents(self, docs: list[Document]) -> None:
        """Reset and (re)build the index over `docs`. Tokenizes each doc.text.

        Reset is unconditional — re-indexing replaces, doesn't accumulate.
        """
        self._postings = {}
        self._doc_freq = {}
        self._doc_lengths = {}
        for doc in docs:
            tokens = tokenize(doc.text)
            self._doc_lengths[doc.doc_id] = len(tokens)
            term_freqs: dict[str, int] = {}
            for t in tokens:
                term_freqs[t] = term_freqs.get(t, 0) + 1
            for term, tf in term_freqs.items():
                self._postings.setdefault(term, []).append(
                    IndexEntry(doc_id=doc.doc_id, term_freq=tf, doc_length=len(tokens))
                )
                self._doc_freq[term] = self._doc_freq.get(term, 0) + 1
        self.num_docs = len(docs)
        total = sum(self._doc_lengths.values())
        # TRUE division: avgdl is a float. Integer division silently poisons every BM25 score.
        self._avg_doc_length = total / len(docs) if docs else 0.0

    def doc_freq(self, term: str) -> int:
        """How many distinct docs the term appears in (0 if unseen)."""
        return self._doc_freq.get(term, 0)

    def postings(self, term: str) -> list[IndexEntry]:
        """Postings list for `term`; empty list if the term is unseen.

        Callers rely on the empty-list-on-miss behavior — don't use [].
        """
        return self._postings.get(term, [])

    def avg_doc_length(self) -> float:
        return self._avg_doc_length

    def prune_rare_terms(self, min_df: int) -> None:
        """Drop terms with doc_freq < min_df from both _postings and _doc_freq.

        Snapshot the keys first — we're mutating the dict we'd otherwise iterate.
        """
        for term, df in list(self._doc_freq.items()):
            if df < min_df:
                del self._doc_freq[term]
                del self._postings[term]
