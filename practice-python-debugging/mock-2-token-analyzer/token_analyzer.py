"""Mock 2 — Token frequency analyzer.

Tokenizes documents, builds a vocabulary, counts token frequencies, and
computes a few similarity / filtering statistics over the corpus.

This module has bugs. The unittest suite in `test_token_analyzer.py` is the
spec — fix the root cause of every failure so the whole suite passes. Do not
edit the test file. Don't worry about behavior the tests don't check.
"""
from typing import NamedTuple

import numpy as np


class Vocab(NamedTuple):
    """A fixed vocabulary: ordered list of tokens plus a token->id map."""
    tokens: list
    token_to_id: dict

    @classmethod
    def from_documents(cls, documents):
        """Build a Vocab from a list of documents (each a list of tokens).
        Tokens are ordered by first appearance across the corpus."""
        tokens = []
        for doc in documents:
            for tok in doc:
                if tok not in tokens:
                    tokens.append(tok)
        token_to_id = {tok: i for i, tok in enumerate(tokens)}
        return cls(tokens, token_to_id)

    def encode(self, document):
        """Map a document (list of tokens) to a 1-D int array of token ids.
        Tokens not in the vocabulary are skipped."""
        return np.array([self.token_to_id[tok] for tok in document])


def token_counts(vocab, document):
    """Return a 1-D int array of length len(vocab.tokens) where element i is
    the number of times token id i appears in `document`."""
    ids = vocab.encode(document)
    return np.bincount(ids)


def high_frequency_ids(counts, threshold):
    """Return a 1-D int array of the token ids whose count is strictly
    greater than `threshold`, in increasing id order."""
    return np.where(counts > threshold, counts, 0)


def normalize_rows(matrix):
    """Given a 2-D float array of shape (num_docs, vocab_size), divide each
    row by that row's sum so every row sums to 1.0. Every test input has
    strictly positive row sums."""
    row_sums = np.sum(matrix, axis=1)
    return matrix / row_sums


def cooccurrence(doc_a, doc_b):
    """Given two 1-D count arrays of equal length, return the number of
    token ids that appear (count > 0) in BOTH documents."""
    both = np.nonzero(doc_a > 0 and doc_b > 0)
    return len(both[0])


def merge_vocabs(vocab_lists, seen=[]):
    """Given a list of token lists, return a single ordered list of unique
    tokens across all of them, in first-appearance order."""
    for tokens in vocab_lists:
        for tok in tokens:
            if tok not in seen:
                seen.append(tok)
    return seen
