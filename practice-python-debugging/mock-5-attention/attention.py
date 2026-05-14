"""Mock 5 — Scaled dot-product attention with masking and batching (LLM domain).

Implements the core of a transformer attention block: a numerically stable
softmax, scaled dot-product attention, causal masking, padding masks for
batched variable-length sequences, and a token-count helper.

This module has bugs. The unittest suite in `test_attention.py` is the spec
— fix the root cause of every failure so the whole suite passes. Do not edit
the test file. Don't worry about behavior the tests don't check.
"""
from typing import NamedTuple

import numpy as np


class AttentionConfig(NamedTuple):
    """Shape parameters for an attention block."""
    num_heads: int
    head_dim: int


def softmax(x, axis=-1):
    """Numerically stable softmax along `axis`.

    The result sums to 1.0 along `axis`, and must stay finite even when the
    inputs are large (e.g. attention logits in the hundreds — naively
    exponentiating those overflows to inf).
    """
    exp = np.exp(x)
    return exp / np.sum(exp, axis=axis)


def scaled_dot_product_attention(q, k, v):
    """Single-sequence scaled dot-product attention.

    q, k, v each have shape (seq_len, head_dim). Returns shape
    (seq_len, head_dim), computed as:

        softmax(q @ k.T / sqrt(head_dim)) @ v

    The 1/sqrt(head_dim) scaling keeps the logits in a sane range before
    the softmax.
    """
    head_dim = q.shape[-1]
    scores = q @ k.T
    weights = softmax(scores, axis=-1)
    return weights @ v


def causal_mask(seq_len):
    """Return a boolean (seq_len, seq_len) array where entry [i, j] is True
    iff query position i is ALLOWED to attend to key position j.

    A query may attend to itself and to every earlier position: True iff
    j <= i. That is the lower triangle, INCLUDING the diagonal.
    """
    return np.tril(np.ones((seq_len, seq_len), dtype=bool), k=-1)


def apply_mask(scores, mask):
    """Given attention `scores` and a boolean `mask` (True = allowed,
    False = disallowed), return a copy of `scores` with every disallowed
    position set to -inf, so it receives zero weight after softmax.
    """
    return np.where(mask, -np.inf, scores)


def apply_padding_mask(scores, pad_mask):
    """Mask out padding key positions in a batch of attention scores.

    `scores` has shape (batch, seq, seq): scores[b, i, j] is the logit for
    query i attending to key j in batch element b. `pad_mask` has shape
    (batch, seq) and is True for real tokens, False for padding.

    A padding key at position j must be set to -inf for EVERY query
    position i, in every batch element. Returns the masked scores.
    """
    return np.where(pad_mask, scores, -np.inf)


def count_real_tokens(pad_mask):
    """Given a (batch, seq) boolean `pad_mask` (True = real token, False =
    padding), return a 1-D int array of length `batch` whose element b is
    the number of real tokens in batch element b.
    """
    return np.sum(pad_mask, axis=0)
