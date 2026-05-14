"""Mock 4 — BPE tokenizer (LLM domain).

Builds a small byte-pair-encoding tokenizer: learns a character vocabulary
from a corpus, applies merge rules to encode text into token ids, and
decodes ids back to text. Also reports token-frequency statistics.

This module has bugs. The unittest suite in `test_bpe_tokenizer.py` is the
spec — fix the root cause of every failure so the whole suite passes. Do not
edit the test file. Don't worry about behavior the tests don't check.
"""
from typing import NamedTuple

import numpy as np


class TokenizerConfig(NamedTuple):
    """Tokenizer hyperparameters."""
    vocab_size: int        # total vocabulary size, INCLUDING the 2 special tokens
    unk_token: str         # rendered for unknown characters
    pad_token: str         # rendered for padding positions


class Vocab(NamedTuple):
    """A learned vocabulary."""
    id_to_token: list      # id_to_token[i] is the token string for id i
    token_to_id: dict      # inverse map
    unk_id: int
    pad_id: int


# Special tokens always occupy the first two ids.
_UNK_ID = 0
_PAD_ID = 1
_NUM_SPECIAL = 2


def build_vocab(corpus, config):
    """Build a Vocab from `corpus` (a list of strings).

    Layout: id 0 = unk_token, id 1 = pad_token, then the most frequent
    characters in the corpus (ties broken by the character itself), filling
    up to exactly config.vocab_size entries total.
    """
    counts = {}
    for word in corpus:
        for ch in word:
            counts[ch] = counts.get(ch, 0) + 1

    # most frequent first; tie-break alphabetically
    ranked = sorted(counts, key=lambda c: (-counts[c], c))
    kept = ranked[: config.vocab_size]

    id_to_token = [config.unk_token, config.pad_token] + kept
    token_to_id = {tok: i for i, tok in enumerate(id_to_token)}
    return Vocab(id_to_token, token_to_id, _PAD_ID, _UNK_ID)


def apply_merges(tokens, merges):
    """Recursively apply BPE merge rules until none apply.

    `tokens` is a list of token strings; `merges` maps an adjacent
    (left, right) pair to its merged token. On each call, find the first
    adjacent pair that has a merge rule, apply it, and recurse on the
    result. When no pair can be merged, return the token list unchanged.
    """
    for i in range(len(tokens) - 2):
        pair = (tokens[i], tokens[i + 1])
        if pair in merges:
            merged = merges[pair]
            new_tokens = tokens[:i] + [merged] + tokens[i + 2:]
            return apply_merges(new_tokens, merges)
    return tokens


class BPETokenizer:
    """Encodes text to token ids and back, using a learned Vocab + merges."""

    def __init__(self, vocab, merges):
        self.vocab = vocab
        self.merges = merges

    def encode(self, text):
        """Encode `text` into a 1-D np.ndarray of token ids.

        Split into characters, apply BPE merges, then map each merged token
        to its id. A token not in the vocabulary maps to unk_id.
        """
        merged = apply_merges(list(text), self.merges)
        ids = [self.vocab.token_to_id[tok] for tok in merged]
        return np.array(ids)

    def decode(self, ids):
        """Decode a sequence of token ids back into a string by
        concatenating each id's token. ids may be a list or np.ndarray."""
        return "".join(self.vocab.id_to_token[i] for i in ids)


def token_frequencies(tokenizer, texts):
    """Return a 1-D int array of length vocab_size where element i is the
    total number of times token id i appears across all encoded `texts`."""
    vocab_size = len(tokenizer.vocab.id_to_token)
    all_ids = []
    for text in texts:
        all_ids.extend(tokenizer.encode(text).tolist())
    return np.bincount(np.array(all_ids))


def non_pad_length(ids, pad_id):
    """Given a 1-D array of token ids, return the count of ids that are NOT
    the padding id."""
    real = np.where(ids != pad_id)
    return len(real)


def compression_ratio(text, ids):
    """Return characters-per-token: len(text) divided by the number of token
    ids. A higher ratio means better compression."""
    return len(text) // len(ids)
