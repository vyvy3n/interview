"""Mock 6 — Token sampler / decoder (LLM domain).

Implements the sampling stack used to turn model logits into generated
tokens: temperature scaling, top-k and top-p (nucleus) filtering, greedy
decoding, a reproducible stochastic sampler, recursive autoregressive
generation, and a perplexity metric.

This module has bugs. The unittest suite in `test_sampler.py` is the spec —
fix the root cause of every failure so the whole suite passes. Do not edit
the test file. Don't worry about behavior the tests don't check.
"""
from typing import NamedTuple

import numpy as np


class GenerationConfig(NamedTuple):
    """Decoding hyperparameters."""
    temperature: float
    top_k: int
    top_p: float
    max_length: int
    seed: int


def apply_temperature(logits, temperature):
    """Scale `logits` by the sampling temperature.

    Higher temperature => a flatter (more uniform) distribution after
    softmax; temperature 1.0 leaves the logits unchanged; temperature < 1.0
    sharpens them.
    """
    return logits * temperature


def top_k_filter(probs, k):
    """Keep only the `k` highest-probability tokens, zero out the rest, and
    renormalize so the result still sums to 1.0."""
    top = np.argsort(probs)[:k]
    keep = np.zeros_like(probs, dtype=bool)
    keep[top] = True
    filtered = np.where(keep, probs, 0.0)
    return filtered / filtered.sum()


def top_p_filter(probs, p):
    """Nucleus filter: keep the smallest set of highest-probability tokens
    whose cumulative probability reaches `p`, zero out the rest, and
    renormalize so the result sums to 1.0.
    """
    order = np.argsort(probs)[::-1]            # token ids, highest prob first
    sorted_probs = probs[order]
    cumulative = np.cumsum(sorted_probs)
    # a token is in the nucleus if the cumulative mass BEFORE it was < p
    keep_sorted = cumulative - sorted_probs < p
    keep = np.zeros_like(probs, dtype=bool)
    keep[order] = keep_sorted
    filtered = np.where(keep, probs, 0.0)
    return filtered


def greedy_next_token(probs):
    """Return the token id (an int) with the highest probability."""
    return np.max(probs)


def surviving_token_ids(probs):
    """Return a 1-D int array of the token ids with nonzero probability,
    in increasing id order."""
    return np.nonzero(probs)


class Sampler:
    """Draws token ids from a probability distribution with a reproducible
    RNG stream. Two Samplers built with the same seed produce identical
    sequences of draws."""

    def __init__(self, seed):
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def sample(self, probs):
        """Draw one token id from the distribution `probs`. Successive calls
        advance the RNG stream, so a run of draws is varied rather than all
        identical."""
        rng = np.random.RandomState(self.seed)
        return int(rng.choice(len(probs), p=probs))


def generate(sampler, prompt, next_probs_fn, max_length):
    """Recursively generate tokens until the sequence reaches `max_length`.

    `prompt` is the starting list of token ids. `next_probs_fn(tokens)`
    returns the probability array for the next token given the sequence so
    far. Returns the full token list, which must have length exactly
    `max_length`.
    """
    if len(prompt) > max_length:
        return prompt
    probs = next_probs_fn(prompt)
    next_token = sampler.sample(probs)
    return generate(sampler, prompt + [next_token], next_probs_fn, max_length)


def perplexity(logprobs):
    """Return the perplexity of a generated sequence: the exponential of the
    negative mean per-token log-probability. Lower is better."""
    mean_logprob = sum(logprobs) / len(logprobs)
    return np.exp(mean_logprob)
