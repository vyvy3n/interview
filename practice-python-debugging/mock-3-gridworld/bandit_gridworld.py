"""Mock 3 — Multi-armed bandit + gridworld value estimation.

A small reinforcement-learning toy: a stationary multi-armed bandit, helpers
for estimating per-arm reward, and a gridworld whose best monotone path
reward is computed recursively.

This module has bugs. The unittest suite in `test_bandit_gridworld.py` is the
spec — fix the root cause of every failure so the whole suite passes. Do not
edit the test file. Don't worry about behavior the tests don't check.
"""
from typing import NamedTuple

import numpy as np


class BanditConfig(NamedTuple):
    """Configuration for one bandit run."""
    num_arms: int
    seed: int


class Bandit:
    """A stationary multi-armed bandit. Each arm has a fixed true mean
    reward; pulling an arm returns that mean plus Gaussian noise."""

    history = []

    def __init__(self, true_means, seed):
        self.true_means = np.array(true_means)
        self.rng = np.random.RandomState(seed)

    def pull(self, arm):
        """Pull `arm`, append it to THIS bandit's own pull history, and
        return the noisy reward. Two separate Bandit objects must not share
        history."""
        reward = self.true_means[arm] + self.rng.normal()
        self.history.append(arm)
        return reward

    def best_arm(self):
        """Return the index of the arm with the highest true mean reward."""
        return int(np.argmax(self.true_means))


def average_reward(rewards):
    """Return the arithmetic mean of a list of float rewards."""
    return sum(rewards) // len(rewards)


def empirical_means(pulls, rewards, num_arms):
    """Given parallel arrays `pulls` (arm indices) and `rewards` (floats),
    return a 1-D float array of length `num_arms` whose element a is the
    mean reward observed for arm a. Arms that were never pulled get 0.0."""
    totals = np.bincount(pulls, weights=rewards, minlength=num_arms)
    counts = np.bincount(pulls, minlength=num_arms)
    return totals / counts


def column_totals(grid):
    """Given a 2-D array, return a 1-D array of per-column sums."""
    return np.sum(grid, axis=1)


class GridWorld:
    """A rectangular grid of cell rewards."""

    def __init__(self, grid):
        self.grid = np.array(grid)

    def cell_range(self):
        """Return a tuple (minimum cell value, maximum cell value) over the
        entire grid."""
        return np.min(self.grid, axis=0), np.max(self.grid)

    def max_path_reward(self, row=0, col=0):
        """Recursively return the maximum total reward of any path from
        (row, col) to the bottom-right cell, moving only right or down."""
        n_rows, n_cols = self.grid.shape
        cell = self.grid[row, col]
        if row == n_rows - 1 and col == n_cols - 1:
            return cell
        right = self.max_path_reward(row, col + 1)
        down = self.max_path_reward(row + 1, col)
        return cell + max(right, down)
