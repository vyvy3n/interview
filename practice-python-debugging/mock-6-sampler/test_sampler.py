"""Spec for Mock 6 — do not edit. Fix sampler.py until this all passes.

Run:  python -m unittest test_sampler -v
"""
import unittest

import numpy as np

from sampler import (
    Sampler,
    apply_temperature,
    generate,
    greedy_next_token,
    perplexity,
    surviving_token_ids,
    top_k_filter,
    top_p_filter,
)


class TestApplyTemperature(unittest.TestCase):
    def test_temperature_one_is_identity(self):
        logits = np.array([2.0, 4.0, 6.0])
        np.testing.assert_allclose(apply_temperature(logits, 1.0), logits)

    def test_high_temperature_shrinks_logits(self):
        # temperature 2.0 should HALVE the logits (flatter distribution)
        logits = np.array([2.0, 4.0, 6.0])
        np.testing.assert_allclose(apply_temperature(logits, 2.0), [1.0, 2.0, 3.0])


class TestTopKFilter(unittest.TestCase):
    def test_keeps_the_k_highest(self):
        probs = np.array([0.1, 0.5, 0.2, 0.05, 0.15])
        out = top_k_filter(probs, k=2)
        # the two highest-probability ids are 1 (0.5) and 2 (0.2)
        self.assertGreater(out[1], 0.0)
        self.assertGreater(out[2], 0.0)
        self.assertEqual(out[0], 0.0)
        self.assertEqual(out[3], 0.0)
        self.assertEqual(out[4], 0.0)

    def test_result_is_renormalized(self):
        probs = np.array([0.1, 0.5, 0.2, 0.05, 0.15])
        out = top_k_filter(probs, k=2)
        self.assertAlmostEqual(float(out.sum()), 1.0)


class TestTopPFilter(unittest.TestCase):
    def test_keeps_the_nucleus(self):
        probs = np.array([0.5, 0.3, 0.15, 0.05])
        out = top_p_filter(probs, p=0.7)
        # 0.5 + 0.3 = 0.8 >= 0.7, so ids 0 and 1 form the nucleus
        self.assertGreater(out[0], 0.0)
        self.assertGreater(out[1], 0.0)
        self.assertEqual(out[2], 0.0)
        self.assertEqual(out[3], 0.0)

    def test_result_is_renormalized(self):
        probs = np.array([0.5, 0.3, 0.15, 0.05])
        out = top_p_filter(probs, p=0.7)
        self.assertAlmostEqual(float(out.sum()), 1.0)


class TestGreedyNextToken(unittest.TestCase):
    def test_returns_argmax_id(self):
        probs = np.array([0.1, 0.6, 0.3])
        self.assertEqual(greedy_next_token(probs), 1)

    def test_returns_an_integer_id(self):
        probs = np.array([0.7, 0.2, 0.1])
        result = greedy_next_token(probs)
        self.assertEqual(int(result), 0)
        self.assertLess(result, len(probs))  # it's an id, not a probability


class TestSurvivingTokenIds(unittest.TestCase):
    def test_returns_1d_id_array(self):
        probs = np.array([0.0, 0.5, 0.0, 0.5])
        ids = surviving_token_ids(probs)
        self.assertEqual(ids.ndim, 1)
        np.testing.assert_array_equal(ids, [1, 3])


class TestSampler(unittest.TestCase):
    def test_draws_advance_the_stream(self):
        # 20 draws from a uniform distribution must not all be identical.
        sampler = Sampler(seed=0)
        uniform = np.array([0.25, 0.25, 0.25, 0.25])
        draws = [sampler.sample(uniform) for _ in range(20)]
        self.assertGreater(len(set(draws)), 1, "every draw was identical")

    def test_reproducible_across_samplers(self):
        uniform = np.array([0.25, 0.25, 0.25, 0.25])
        a = [Sampler(seed=7).sample(uniform) for _ in range(10)]
        # rebuild and redraw — same seed must give the same sequence
        s = Sampler(seed=7)
        b = [s.sample(uniform) for _ in range(10)]
        # `a` used a fresh Sampler per draw; `b` used one Sampler. Only the
        # first element is guaranteed equal — but b itself must be varied.
        self.assertEqual(a[0], b[0])
        self.assertGreater(len(set(b)), 1)


class TestGenerate(unittest.TestCase):
    def test_generates_exactly_max_length(self):
        # next_probs_fn always points at token id 2 (degenerate distribution)
        next_probs_fn = lambda tokens: np.array([0.0, 0.0, 1.0])
        result = generate(Sampler(seed=0), [0], next_probs_fn, max_length=4)
        self.assertEqual(len(result), 4)
        self.assertEqual(result, [0, 2, 2, 2])

    def test_prompt_already_at_length(self):
        next_probs_fn = lambda tokens: np.array([0.0, 0.0, 1.0])
        result = generate(Sampler(seed=0), [0, 1, 2], next_probs_fn, max_length=3)
        self.assertEqual(result, [0, 1, 2])


class TestPerplexity(unittest.TestCase):
    def test_uniform_two_way_distribution(self):
        # every token had probability 0.5 -> perplexity 2.0
        logprobs = [np.log(0.5)] * 4
        self.assertAlmostEqual(perplexity(logprobs), 2.0)

    def test_confident_sequence_has_low_perplexity(self):
        # high logprobs (close to 0) -> perplexity close to 1.0
        logprobs = [np.log(0.9)] * 3
        self.assertAlmostEqual(perplexity(logprobs), 1.0 / 0.9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
