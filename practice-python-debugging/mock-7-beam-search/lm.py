"""Provided toy language model for Mock 7 — DO NOT MODIFY.

A language model assigns, for any sequence of tokens, a probability
distribution over what the next token could be. `next_logprobs` returns
that distribution as LOG-probabilities (one negative number per vocab
token) for the token following a given sequence.

This toy model is a *bigram* model: its prediction depends only on the
single last token of the sequence — `_TRANSITION[last_token]` is the
logprob row for whatever comes next. Real LMs condition on the whole
context; this one is deliberately tiny so expected values are hand-checkable.
"""
import numpy as np

VOCAB_SIZE = 4
EOS_ID = 3

# Bigram logprobs: row = previous token id, col = next token id.
# Values are log-probabilities (all negative). Row 3 (EOS) loops to EOS.
_TRANSITION = np.array([
    [-2.30, -0.36, -1.61, -2.30],   # after token 0
    [-1.20, -2.30, -0.36, -2.30],   # after token 1
    [-2.30, -1.61, -2.30, -0.22],   # after token 2
    [-9.00, -9.00, -9.00, -0.01],   # after token 3 (EOS) — strongly self-loops
])

def next_logprobs(tokens):
    """1-D logprob array over the vocabulary for the next token, given the
    sequence so far. This toy LM depends only on the last token."""
    return _TRANSITION[tokens[-1]]
