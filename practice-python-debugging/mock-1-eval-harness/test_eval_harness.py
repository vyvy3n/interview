"""Spec for Mock 1 — do not edit. Fix eval_harness.py until this all passes.

Run:  python -m unittest test_eval_harness -v
"""
import unittest

import numpy as np

from eval_harness import (
    EvalConfig,
    LabelSampler,
    LabelStats,
    flatten_scores,
    make_config,
    passing_indices,
    per_sample_totals,
)


class TestMakeConfig(unittest.TestCase):
    def test_fields_assigned_by_name(self):
        cfg = make_config(num_classes=10, num_samples=100, seed=7)
        self.assertEqual(cfg.num_classes, 10)
        self.assertEqual(cfg.num_samples, 100)
        self.assertEqual(cfg.seed, 7)


class TestLabelSampler(unittest.TestCase):
    def test_sample_shape_and_range(self):
        cfg = EvalConfig(num_classes=5, num_samples=50, seed=0)
        labels = LabelSampler(cfg).sample()
        self.assertEqual(labels.shape, (50,))
        self.assertGreaterEqual(int(labels.min()), 0)
        self.assertLess(int(labels.max()), 5)

    def test_reproducible_across_instances(self):
        cfg = EvalConfig(num_classes=5, num_samples=50, seed=42)
        first = LabelSampler(cfg).sample()
        second = LabelSampler(cfg).sample()
        np.testing.assert_array_equal(first, second)

    def test_isolated_from_global_rng(self):
        cfg = EvalConfig(num_classes=5, num_samples=50, seed=42)
        first = LabelSampler(cfg).sample()
        np.random.seed(999)  # mutating the global RNG must not affect the sampler
        second = LabelSampler(cfg).sample()
        np.testing.assert_array_equal(first, second)


class TestLabelStats(unittest.TestCase):
    def test_counts_shape_when_top_class_absent(self):
        labels = np.array([0, 1, 2, 3, 0, 1])  # class 4 never appears
        stats = LabelStats.from_labels(labels, num_classes=5)
        self.assertEqual(stats.counts.shape, (5,))

    def test_counts_values(self):
        labels = np.array([0, 0, 1, 2, 2, 2])
        stats = LabelStats.from_labels(labels, num_classes=4)
        np.testing.assert_array_equal(stats.counts, [2, 1, 3, 0])

    def test_fractions_sum_to_one(self):
        labels = np.array([0, 0, 1, 2, 2, 2])
        stats = LabelStats.from_labels(labels, num_classes=4)
        self.assertAlmostEqual(float(stats.fractions().sum()), 1.0)

    def test_fractions_values(self):
        labels = np.array([0, 0, 1, 1])
        stats = LabelStats.from_labels(labels, num_classes=2)
        np.testing.assert_allclose(stats.fractions(), [0.5, 0.5])

    def test_most_common(self):
        labels = np.array([0, 0, 1, 2, 2, 2])
        stats = LabelStats.from_labels(labels, num_classes=4)
        self.assertEqual(stats.most_common(), 2)


class TestPerSampleTotals(unittest.TestCase):
    def test_row_sums(self):
        matrix = np.array([[1, 2, 3], [4, 5, 6]])
        np.testing.assert_array_equal(per_sample_totals(matrix), [6, 15])

    def test_single_row(self):
        matrix = np.array([[10, 20, 30]])
        np.testing.assert_array_equal(per_sample_totals(matrix), [60])


class TestPassingIndices(unittest.TestCase):
    def test_returns_1d_index_array(self):
        scores = np.array([0.1, 0.9, 0.4, 0.8])
        idx = passing_indices(scores, 0.5)
        self.assertEqual(idx.ndim, 1)
        np.testing.assert_array_equal(idx, [1, 3])

    def test_none_passing(self):
        scores = np.array([0.1, 0.2, 0.3])
        idx = passing_indices(scores, 0.9)
        self.assertEqual(idx.ndim, 1)
        self.assertEqual(len(idx), 0)


class TestFlattenScores(unittest.TestCase):
    def test_already_flat(self):
        self.assertEqual(flatten_scores([1, 2, 3]), [1, 2, 3])

    def test_nested(self):
        self.assertEqual(flatten_scores([1, [2, 3], [[4], 5]]), [1, 2, 3, 4, 5])

    def test_deeply_nested(self):
        self.assertEqual(flatten_scores([[[[1]]], 2]), [1, 2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
