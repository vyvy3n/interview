"""Spec for Mock 2 — do not edit. Fix token_analyzer.py until this all passes.

Run:  python -m unittest test_token_analyzer -v
"""
import unittest

import numpy as np

from token_analyzer import (
    Vocab,
    cooccurrence,
    high_frequency_ids,
    merge_vocabs,
    normalize_rows,
    token_counts,
)


class TestVocab(unittest.TestCase):
    def test_from_documents_orders_by_first_appearance(self):
        vocab = Vocab.from_documents([["b", "a"], ["a", "c", "b"]])
        self.assertEqual(vocab.tokens, ["b", "a", "c"])
        self.assertEqual(vocab.token_to_id, {"b": 0, "a": 1, "c": 2})

    def test_encode_known_tokens(self):
        vocab = Vocab.from_documents([["x", "y", "z"]])
        np.testing.assert_array_equal(vocab.encode(["z", "x", "x"]), [2, 0, 0])

    def test_encode_skips_unknown_tokens(self):
        vocab = Vocab.from_documents([["x", "y"]])
        # "q" is not in the vocabulary — it should be skipped, not crash.
        np.testing.assert_array_equal(vocab.encode(["x", "q", "y", "q"]), [0, 1])


class TestTokenCounts(unittest.TestCase):
    def test_counts_full_length(self):
        vocab = Vocab.from_documents([["a", "b", "c", "d"]])
        # document only uses ids 0 and 1, but counts must cover all 4 tokens
        counts = token_counts(vocab, ["a", "a", "b"])
        self.assertEqual(counts.shape, (4,))
        np.testing.assert_array_equal(counts, [2, 1, 0, 0])


class TestHighFrequencyIds(unittest.TestCase):
    def test_returns_ids_above_threshold(self):
        counts = np.array([5, 0, 3, 9, 1])
        np.testing.assert_array_equal(high_frequency_ids(counts, 2), [0, 2, 3])

    def test_returns_1d_id_array(self):
        counts = np.array([5, 0, 3, 9, 1])
        ids = high_frequency_ids(counts, 2)
        self.assertEqual(ids.ndim, 1)

    def test_none_above_threshold(self):
        counts = np.array([1, 1, 1])
        self.assertEqual(len(high_frequency_ids(counts, 10)), 0)


class TestNormalizeRows(unittest.TestCase):
    def test_rows_sum_to_one(self):
        matrix = np.array([[1.0, 1.0, 2.0], [2.0, 2.0, 6.0]])
        out = normalize_rows(matrix)
        np.testing.assert_allclose(out.sum(axis=1), [1.0, 1.0])

    def test_values(self):
        matrix = np.array([[1.0, 1.0, 2.0], [3.0, 3.0, 4.0]])
        out = normalize_rows(matrix)
        np.testing.assert_allclose(
            out, [[0.25, 0.25, 0.5], [0.3, 0.3, 0.4]]
        )


class TestCooccurrence(unittest.TestCase):
    def test_counts_shared_nonzero_ids(self):
        doc_a = np.array([1, 0, 2, 0, 3])
        doc_b = np.array([0, 0, 5, 1, 1])
        # shared nonzero positions: id 2 and id 4 -> 2
        self.assertEqual(cooccurrence(doc_a, doc_b), 2)

    def test_no_overlap(self):
        doc_a = np.array([1, 0, 1, 0])
        doc_b = np.array([0, 1, 0, 1])
        self.assertEqual(cooccurrence(doc_a, doc_b), 0)


class TestMergeVocabs(unittest.TestCase):
    def test_merges_in_first_appearance_order(self):
        result = merge_vocabs([["a", "b"], ["b", "c"], ["a", "d"]])
        self.assertEqual(result, ["a", "b", "c", "d"])

    def test_independent_across_calls(self):
        # Each call must start fresh — no state leaking from a previous call.
        first = merge_vocabs([["x", "y"]])
        second = merge_vocabs([["p", "q"]])
        self.assertEqual(first, ["x", "y"])
        self.assertEqual(second, ["p", "q"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
