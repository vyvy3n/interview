"""Spec for Mock 5 — do not edit. Fix attention.py until this all passes.

Run:  python -m unittest test_attention -v
"""
import unittest

import numpy as np

from attention import (
    apply_mask,
    apply_padding_mask,
    causal_mask,
    count_real_tokens,
    scaled_dot_product_attention,
    softmax,
)


class TestSoftmax(unittest.TestCase):
    def test_small_1d(self):
        out = softmax(np.array([1.0, 2.0, 3.0]))
        self.assertAlmostEqual(float(out.sum()), 1.0)
        self.assertTrue(np.all(out > 0))

    def test_large_values_stay_finite(self):
        # Naive exp() of these overflows to inf -> nan. A stable softmax
        # subtracts the max first.
        out = softmax(np.array([1000.0, 1001.0, 1002.0]))
        self.assertTrue(np.all(np.isfinite(out)), f"softmax overflowed: {out}")
        self.assertAlmostEqual(float(out.sum()), 1.0)

    def test_2d_rows_sum_to_one(self):
        x = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        out = softmax(x, axis=-1)
        self.assertEqual(out.shape, (2, 3))
        np.testing.assert_allclose(out.sum(axis=-1), [1.0, 1.0])


class TestScaledDotProductAttention(unittest.TestCase):
    def test_matches_scaled_formula(self):
        q = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
        k = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
        v = np.array([[1.0, 1.0, 1.0, 1.0], [2.0, 2.0, 2.0, 2.0]])
        out = scaled_dot_product_attention(q, k, v)

        # Reference: scores must be divided by sqrt(head_dim) before softmax.
        head_dim = 4
        scores = q @ k.T / np.sqrt(head_dim)
        e = np.exp(scores - scores.max(axis=-1, keepdims=True))
        weights = e / e.sum(axis=-1, keepdims=True)
        expected = weights @ v

        np.testing.assert_allclose(out, expected)


class TestCausalMask(unittest.TestCase):
    def test_diagonal_is_allowed(self):
        # A position must be allowed to attend to itself.
        m = causal_mask(3)
        for i in range(3):
            self.assertTrue(m[i, i], f"position {i} cannot attend to itself")

    def test_no_attending_to_the_future(self):
        m = causal_mask(3)
        self.assertFalse(m[0, 1])
        self.assertFalse(m[1, 2])

    def test_can_attend_to_the_past(self):
        m = causal_mask(3)
        self.assertTrue(m[1, 0])
        self.assertTrue(m[2, 0])


class TestApplyMask(unittest.TestCase):
    def test_disallowed_positions_become_neg_inf(self):
        scores = np.array([[1.0, 2.0], [3.0, 4.0]])
        mask = np.array([[True, False], [False, True]])
        out = apply_mask(scores, mask)
        # mask True = allowed -> keep the score; False = disallowed -> -inf
        np.testing.assert_array_equal(
            out, np.array([[1.0, -np.inf], [-np.inf, 4.0]])
        )


class TestApplyPaddingMask(unittest.TestCase):
    def test_padding_keys_masked_for_every_query(self):
        scores = np.ones((2, 3, 3))
        pad_mask = np.array([[True, True, False], [True, False, False]])
        out = apply_padding_mask(scores, pad_mask)
        # batch 0: key position 2 is padding -> -inf for all queries
        self.assertTrue(np.all(out[0, :, 2] == -np.inf))
        self.assertTrue(np.all(out[0, :, :2] == 1.0))
        # batch 1: key positions 1 and 2 are padding
        self.assertTrue(np.all(out[1, :, 1:] == -np.inf))
        self.assertTrue(np.all(out[1, :, 0] == 1.0))


class TestCountRealTokens(unittest.TestCase):
    def test_per_batch_element_count(self):
        pad_mask = np.array([[True, True, False], [True, False, False]])
        out = count_real_tokens(pad_mask)
        np.testing.assert_array_equal(out, [2, 1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
