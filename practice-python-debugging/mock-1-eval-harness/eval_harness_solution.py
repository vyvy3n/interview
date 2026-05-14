"""Mock 1 — Research evaluation harness.

Samples synthetic class labels, aggregates them into per-class counts, and
computes simple summary statistics over an evaluation run.

This module has bugs. The unittest suite in `test_eval_harness.py` is the
spec — fix the root cause of every failure so the whole suite passes. Do not
edit the test file. Don't worry about behavior the tests don't check.
"""
from typing import NamedTuple

import numpy as np


class EvalConfig(NamedTuple):
    """Configuration for one evaluation run."""
    num_classes: int
    num_samples: int
    seed: int


def make_config(num_classes, num_samples, seed):
    """Build an EvalConfig from the three run parameters."""
    return EvalConfig(num_classes, num_samples, seed)


class LabelSampler:
    """Draws synthetic integer class labels in the range [0, num_classes)."""

    def __init__(self, config):
        self.config = config
        self.rng = np.random.RandomState(config.seed)

    def sample(self):
        """Return a 1-D int array of length num_samples, each value in
        [0, num_classes). Two samplers built from the same config must
        produce identical arrays, regardless of any other RNG use."""

        return self.rng.randint(
            0, self.config.num_classes, size=self.config.num_samples
        )


class LabelStats(NamedTuple):
    """Per-class aggregate statistics over a batch of labels."""
    num_classes: int
    counts: np.ndarray

    @classmethod
    def from_labels(cls, labels, num_classes):
        """Aggregate `labels` into a per-class count array. `counts` must
        have shape (num_classes,) even if some classes never appear."""
        counts = np.bincount(labels, minlength=num_classes)
        return cls(num_classes=num_classes, counts=counts)

    def fractions(self):
        """Return the per-class fraction of the total, shape (num_classes,).
        The returned array sums to 1.0 (when at least one label was seen)."""
        return self.counts / sum(self.counts)

    def most_common(self):
        """Return the class id with the highest count."""
        return int(np.argmax(self.counts))


def per_sample_totals(matrix):
    """Given a 2-D array of shape (num_samples, num_features), return a 1-D
    array of length num_samples whose element i is the sum of row i."""
    return np.sum(matrix, axis=1)


def passing_indices(scores, threshold):
    """Return a 1-D int array of the indices i where scores[i] > threshold,
    in increasing order."""
    return np.where(scores > threshold)[0]


def flatten_scores(nested):
    """Recursively flatten an arbitrarily nested list of numbers into a
    single flat list, preserving left-to-right order."""
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(flatten_scores(item))
        else:
            flat.append(item)
    return flat
