"""Spec for Mock 4 — do not edit. Fix bpe_tokenizer.py until this all passes.

Run:  python -m unittest test_bpe_tokenizer -v
"""
import unittest

import numpy as np

from bpe_tokenizer import (
    BPETokenizer,
    TokenizerConfig,
    Vocab,
    apply_merges,
    build_vocab,
    compression_ratio,
    non_pad_length,
    token_frequencies,
)


class TestBuildVocab(unittest.TestCase):
    def setUp(self):
        # "hello world" has 8 distinct characters: h e l o (space) w r d
        self.corpus = ["hello world"]
        self.config = TokenizerConfig(vocab_size=5, unk_token="<unk>", pad_token="<pad>")

    def test_vocab_size_includes_specials(self):
        # vocab_size=5 means 2 special tokens + 3 learned characters.
        vocab = build_vocab(self.corpus, self.config)
        self.assertEqual(len(vocab.id_to_token), 5)

    def test_special_token_ids(self):
        vocab = build_vocab(self.corpus, self.config)
        self.assertEqual(vocab.unk_id, 0)
        self.assertEqual(vocab.pad_id, 1)
        self.assertEqual(vocab.id_to_token[0], "<unk>")
        self.assertEqual(vocab.id_to_token[1], "<pad>")

    def test_most_frequent_chars_kept(self):
        # 'l' appears 3x and 'o' 2x — they must be among the 3 learned tokens.
        vocab = build_vocab(self.corpus, self.config)
        self.assertIn("l", vocab.token_to_id)
        self.assertIn("o", vocab.token_to_id)


class TestApplyMerges(unittest.TestCase):
    def setUp(self):
        self.merges = {("a", "b"): "ab", ("ab", "c"): "abc"}

    def test_no_applicable_merges(self):
        self.assertEqual(apply_merges(["c", "c"], self.merges), ["c", "c"])

    def test_merges_including_last_pair(self):
        # a+b -> ab, then ab+c -> abc. The second merge is the LAST pair.
        self.assertEqual(apply_merges(["a", "b", "c"], self.merges), ["abc"])

    def test_merge_at_nonzero_index(self):
        # the only applicable pair is ("a","b") at index 1.
        self.assertEqual(apply_merges(["x", "a", "b"], self.merges), ["x", "ab"])


class TestEncodeDecode(unittest.TestCase):
    def setUp(self):
        id_to_token = ["<unk>", "<pad>", "a", "b", "c", "ab", "abc"]
        token_to_id = {t: i for i, t in enumerate(id_to_token)}
        self.vocab = Vocab(id_to_token, token_to_id, unk_id=0, pad_id=1)
        self.merges = {("a", "b"): "ab", ("ab", "c"): "abc"}
        self.tok = BPETokenizer(self.vocab, self.merges)

    def test_encode_applies_all_merges(self):
        # "abc" should merge all the way to the single token "abc" (id 6).
        np.testing.assert_array_equal(self.tok.encode("abc"), [6])

    def test_encode_unknown_char_maps_to_unk(self):
        # "z" is not in the vocab -> unk_id (0). "ab" merges to id 5.
        np.testing.assert_array_equal(self.tok.encode("abz"), [5, 0])

    def test_decode_roundtrip(self):
        self.assertEqual(self.tok.decode(np.array([2, 3, 4])), "abc")
        self.assertEqual(self.tok.decode([6]), "abc")


class TestTokenFrequencies(unittest.TestCase):
    def setUp(self):
        id_to_token = ["<unk>", "<pad>", "a", "b", "c", "ab", "abc"]
        token_to_id = {t: i for i, t in enumerate(id_to_token)}
        vocab = Vocab(id_to_token, token_to_id, unk_id=0, pad_id=1)
        self.tok = BPETokenizer(vocab, merges={})

    def test_frequencies_cover_full_vocab(self):
        # only token id 4 ("c") is ever used, but the result must still span
        # the whole vocabulary (length 7).
        freqs = token_frequencies(self.tok, ["c", "c", "c"])
        self.assertEqual(freqs.shape, (7,))
        self.assertEqual(int(freqs[4]), 3)


class TestNonPadLength(unittest.TestCase):
    def test_counts_non_pad(self):
        ids = np.array([0, 1, 2, 1, 3])  # pad_id is 1 -> 3 real tokens
        self.assertEqual(non_pad_length(ids, pad_id=1), 3)

    def test_all_pad(self):
        ids = np.array([1, 1, 1])
        self.assertEqual(non_pad_length(ids, pad_id=1), 0)


class TestCompressionRatio(unittest.TestCase):
    def test_ratio_is_fractional(self):
        # 5 characters, 2 tokens -> 2.5 chars per token
        self.assertAlmostEqual(compression_ratio("abcde", np.array([1, 2])), 2.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
