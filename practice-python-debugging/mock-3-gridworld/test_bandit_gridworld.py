"""Spec for Mock 3 — do not edit. Fix bandit_gridworld.py until this passes.

Run:  python -m unittest test_bandit_gridworld -v
"""
import unittest

import numpy as np

from bandit_gridworld import (
    Bandit,
    GridWorld,
    average_reward,
    column_totals,
    empirical_means,
)


class TestBandit(unittest.TestCase):
    def test_pull_returns_float(self):
        b = Bandit(true_means=[0.0, 1.0, 2.0], seed=0)
        reward = b.pull(1)
        self.assertIsInstance(float(reward), float)

    def test_best_arm(self):
        b = Bandit(true_means=[0.3, 0.9, 0.1, 0.5], seed=0)
        self.assertEqual(b.best_arm(), 1)

    def test_history_is_per_instance(self):
        first = Bandit(true_means=[1.0, 2.0], seed=0)
        second = Bandit(true_means=[1.0, 2.0], seed=1)
        first.pull(0)
        first.pull(1)
        second.pull(0)
        # Each bandit tracks only its own pulls.
        self.assertEqual(first.history, [0, 1])
        self.assertEqual(second.history, [0])


class TestAverageReward(unittest.TestCase):
    def test_mean_of_floats(self):
        self.assertAlmostEqual(average_reward([1.5, 2.5, 3.5]), 2.5)

    def test_mean_is_not_floored(self):
        # mean of these is 2.6 — an integer-division bug would give 2.0
        self.assertAlmostEqual(average_reward([1.0, 2.0, 4.8]), 2.6)


class TestEmpiricalMeans(unittest.TestCase):
    def test_basic_means(self):
        pulls = np.array([0, 0, 1, 2])
        rewards = np.array([1.0, 3.0, 10.0, 5.0])
        result = empirical_means(pulls, rewards, num_arms=3)
        np.testing.assert_allclose(result, [2.0, 10.0, 5.0])

    def test_never_pulled_arm_is_zero(self):
        pulls = np.array([0, 0, 2])
        rewards = np.array([2.0, 4.0, 9.0])
        # arm 1 was never pulled -> 0.0, not nan
        result = empirical_means(pulls, rewards, num_arms=3)
        np.testing.assert_allclose(result, [3.0, 0.0, 9.0])


class TestColumnTotals(unittest.TestCase):
    def test_column_sums(self):
        grid = np.array([[1, 2, 3], [4, 5, 6]])
        np.testing.assert_array_equal(column_totals(grid), [5, 7, 9])


class TestGridWorld(unittest.TestCase):
    def test_cell_range(self):
        gw = GridWorld([[3, 1, 4], [1, 5, 9], [2, 6, 5]])
        low, high = gw.cell_range()
        self.assertEqual(int(low), 1)
        self.assertEqual(int(high), 9)

    def test_max_path_reward_single_cell(self):
        gw = GridWorld([[7]])
        self.assertEqual(gw.max_path_reward(), 7)

    def test_max_path_reward_2x2(self):
        # paths: 1->2->4 = 7 ; 1->3->4 = 8  -> best is 8
        gw = GridWorld([[1, 2], [3, 4]])
        self.assertEqual(gw.max_path_reward(), 8)

    def test_max_path_reward_3x3(self):
        gw = GridWorld([[1, 3, 1], [1, 5, 1], [4, 2, 1]])
        # best monotone path: 1->3->5->2->1 = 12
        self.assertEqual(gw.max_path_reward(), 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
