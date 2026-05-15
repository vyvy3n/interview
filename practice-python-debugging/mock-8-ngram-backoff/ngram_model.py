"""Mock 8 — N-gram language model with recursive backoff. [HARD — gap-filler] — REFERENCE SOLUTION.

This is the clean, correct implementation. `ngram_model.py` is this file
with 8 bugs planted. Use this to derive expected values.

WHAT IS AN N-GRAM LANGUAGE MODEL?
---------------------------------
A language model assigns a probability to the next token given the tokens
before it. An *n-gram* model makes a simplifying assumption: the next token
depends only on the previous (n-1) tokens — that fixed-length window of
preceding tokens is called the **context**.

  - n=1 (unigram): no context at all. P(token) is just how often the token
    appeared, overall.
  - n=2 (bigram): context is the 1 token immediately before.
  - n=3 (trigram): context is the 2 tokens immediately before.

COUNTS AND THE MLE ESTIMATE
---------------------------
Training is pure counting. For every position in every sentence we record
"context C was followed by token T". The maximum-likelihood estimate (MLE)
of P(T | C) is then just:

    P(T | C) = count(C, T) / sum over all T' of count(C, T')
             = "how often C->T"  /  "how often C was followed by anything"

STUPID BACKOFF
--------------
Problem: a long context may never have been seen in training, so its counts
are empty and the MLE is 0/0 — undefined. "Stupid backoff" handles this by
falling back to a shorter context:

  - If the FULL context was seen with this token, use weight * MLE.
  - Otherwise, drop the OLDEST (left-most) context token, multiply the
    running weight by `backoff_weight` (a number < 1, so each backoff step
    is penalised), and try again with the shorter context.
  - The recursion bottoms out at the EMPTY context: there we return the
    plain unigram MLE (scaled by whatever weight we accumulated). The empty
    context is the base case — it is ALWAYS defined as long as anything was
    trained.

So "stupid backoff" is a recursion: each step either answers from the
current context or shortens the context by one (from the left) and recurses.

LOGPROB AND PERPLEXITY
----------------------
`logprob` is just log(prob). A probability of exactly 0 has no logarithm
(log(0) = -inf), which would poison any downstream average — so a zero
probability is floored to a large finite negative number, -100.0.

`perplexity` of a sentence is exp(-mean(logprob)) over its tokens, where
each token is scored against its growing left context. Lower perplexity =
the model found the sentence less surprising. Because every logprob is
finite (thanks to the -100.0 floor), perplexity is always a finite number.

A reader who has never seen an n-gram model should be able to learn the
whole idea from this docstring plus `test_ngram_model.py`.
"""
from typing import NamedTuple
import numpy as np


class NGramConfig(NamedTuple):
    n: int                  # order: use up to (n-1) tokens of context
    backoff_weight: float   # multiplier applied each time we back off


class NGramModel:
    def __init__(self, config):
        self.config = config
        self._counts = {}      # context tuple -> {token: count}
        self._vocab = None     # cached set of all tokens seen; lazily built

    def train(self, corpus):
        """corpus: list of sentences (each a list of token strings). Counts
        every k-gram for k = 1..n. Re-training REPLACES prior counts."""
        self._counts = {}
        for sentence in corpus:
            for k in range(1, self.config.n + 1):
                for i in range(len(sentence) - k + 1):
                    context = tuple(sentence[i:i + k - 1])
                    token = sentence[i + k - 1]
                    self._counts.setdefault(context, {})
                    self._counts[context][token] = self._counts[context].get(token, 0) + 1

    @property
    def vocab(self):
        """All distinct tokens seen in training (cached, lazily)."""
        if self._vocab is None:
            self._vocab = set()
            for ctx_counts in self._counts.values():
                self._vocab |= set(ctx_counts)
        return self._vocab

    def prob(self, context, token):
        """P(token | context) via stupid backoff."""
        context = tuple(context)[-(self.config.n - 1):]   # keep the most recent (n-1) tokens
        return self._backoff_prob(context, token, 1.0)

    def _backoff_prob(self, context, token, weight):
        """Recursive backoff. Base case (empty context): the unigram MLE.
        Otherwise: if `context` was seen with `token`, return weight*MLE;
        else drop the OLDEST context token, scale weight, and recurse."""
        if len(context) == 0:
            return 0.0
        ctx_counts = self._counts.get(context)
        if ctx_counts and token in ctx_counts:
            total = sum(ctx_counts.values())
            return weight * ctx_counts[token] / total
        return self._backoff_prob(context[:-1], token, weight * self.config.backoff_weight)

    def logprob(self, context, token):
        """log P(token | context). A zero probability is floored to -100.0
        (a large finite negative) so downstream means stay finite."""
        return float(np.log(self.prob(context, token)))

    def perplexity(self, sentence):
        """exp(-mean logprob) over the sentence, each token scored against
        its growing left context."""
        logps = []
        for i in range(len(sentence)):
            context = sentence[max(0, i - (self.config.n - 1)):i]
            logps.append(self.logprob(context, sentence[i]))
        return float(np.exp(-np.mean(logps)))

    def prune_rare(self, min_count):
        """Drop every (context, token) entry whose count is below min_count."""
        for context, ctx_counts in self._counts.items():
            for token, count in ctx_counts.items():
                if count < min_count:
                    del ctx_counts[token]

    def token_index(self):
        """Map each DISTINCT token to a contiguous id 0..V-1 (sorted order)."""
        all_tokens = [tok for ctx in self._counts.values() for tok in ctx]
        return {tok: i for i, tok in enumerate(all_tokens)}

    def smoothed_probs(self, context):
        """Probabilities over the sorted vocab, floored elementwise at 1e-6
        so none is exactly zero."""
        vocab = sorted(self.vocab)
        probs = np.array([self.prob(context, t) for t in vocab])
        return np.max(probs, 1e-6)

    def increase_order(self):
        """Bump the n-gram order by 1 (returns nothing; updates self.config)."""
        self.config.n += 1
