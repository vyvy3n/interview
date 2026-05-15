"""Spec for Mock 8 — do not edit. Fix ngram_model.py until this all passes.

Run:  python -m unittest test_ngram_model -v

This is the unambiguous spec for the n-gram language model with recursive
stupid-backoff. Every expected value below was derived by running the
reference solution; they are hardcoded so the suite does not depend on the
solution file.

READING THIS FILE AS A TUTORIAL
-------------------------------
The test classes are ordered to teach n-gram modeling by example, simplest
first. Read them top to bottom:

  TestTraining     — training is counting. Every k-gram (k = 1..n) is
                     tallied into a `context -> {token: count}` table.
                     Re-training replaces the table AND must refresh the
                     cached vocab.
  TestProbBackoff  — P(token | context) by MLE: count(ctx, tok) / total.
                     When the full context was never seen, "stupid
                     backoff" drops the OLDEST context token, scales the
                     weight, and retries the shorter context.
  TestBackoffBase  — the recursion base case: the EMPTY context returns
                     the plain unigram MLE. A token reachable only by
                     backing off all the way must still get its real
                     unigram probability — never 0.
  TestLogprob      — log(prob), with prob 0 floored to a finite -100.0 so
                     it cannot poison a downstream mean.
  TestPerplexity   — exp(-mean logprob) over a sentence; always finite.
  TestUtilities    — prune_rare, token_index, smoothed_probs,
                     increase_order: small helpers, each with its own
                     correctness contract.

THE SHARED CORPUS
-----------------
Most tests train a trigram model (n=3) on this 4-sentence corpus:

    ['a', 'b', 'c']
    ['a', 'b', 'd']
    ['a', 'b', 'c']
    ['b', 'c', 'a']

Counting every k-gram for k = 1, 2, 3 gives this table (you can verify it
by hand — that is the point):

    ()          {'a': 4, 'b': 4, 'c': 3, 'd': 1}   <- unigrams, total 12
    ('a',)      {'b': 3}
    ('b',)      {'c': 3, 'd': 1}
    ('c',)      {'a': 1}
    ('a', 'b')  {'c': 2, 'd': 1}
    ('b', 'c')  {'a': 1}

Someone who reads only this file should come away understanding how an
n-gram model and stupid backoff work.
"""
import math
import unittest

from ngram_model import NGramModel, NGramConfig


CORPUS = [
    ['a', 'b', 'c'],
    ['a', 'b', 'd'],
    ['a', 'b', 'c'],
    ['b', 'c', 'a'],
]


def trigram_model():
    """A trigram model (n=3, backoff_weight=0.4) trained on CORPUS."""
    m = NGramModel(NGramConfig(n=3, backoff_weight=0.4))
    m.train(CORPUS)
    return m


class TestTraining(unittest.TestCase):
    """STEP 1 — training is counting.

    `train` walks every sentence and tallies every k-gram for k = 1..n into
    a `context -> {token: count}` table. Re-training REPLACES the table —
    and must also drop the lazily-cached vocab so stale tokens don't linger.
    """

    def test_counts_table_is_built_for_all_k(self):
        """Training counts unigrams, bigrams and trigrams. The empty context
        holds the unigram counts; longer contexts hold the higher k-grams."""
        m = trigram_model()
        self.assertEqual(m._counts[()], {'a': 4, 'b': 4, 'c': 3, 'd': 1})
        self.assertEqual(m._counts[('a',)], {'b': 3})
        self.assertEqual(m._counts[('a', 'b')], {'c': 2, 'd': 1})

    def test_vocab_is_the_distinct_token_set(self):
        """`vocab` is every distinct token seen anywhere in training."""
        m = trigram_model()
        self.assertEqual(m.vocab, {'a', 'b', 'c', 'd'})

    def test_retrain_refreshes_vocab_cache(self):
        """`vocab` is cached lazily — but re-training on a NEW corpus must
        invalidate that cache. After retraining, `vocab` must reflect the
        new corpus only, not a stale union with the old one."""
        # Bug 1: train must invalidate the cached _vocab. The vocab property
        # itself looks correct; the bug is the missing cache reset in train.
        m = NGramModel(NGramConfig(n=2, backoff_weight=0.4))
        m.train([['x', 'y']])
        self.assertEqual(m.vocab, {'x', 'y'})   # builds + caches the vocab
        m.train([['p', 'q', 'r']])              # brand-new corpus
        self.assertEqual(m.vocab, {'p', 'q', 'r'})


class TestProbBackoff(unittest.TestCase):
    """STEP 2 — P(token | context) via MLE and stupid backoff.

    If the full context was seen with the token, the probability is the
    plain MLE count(ctx, tok) / total, scaled by the running weight (1.0 at
    the top level). If the full context was NOT seen, stupid backoff drops
    the OLDEST (left-most) context token, multiplies the weight by
    `backoff_weight`, and retries the shorter context.
    """

    def test_full_context_uses_plain_mle(self):
        """The trigram context ('a','b') was seen 3 times: 2x followed by
        'c', 1x by 'd'. So P('c' | a,b) = 2/3 and P('d' | a,b) = 1/3, with
        no backoff and weight 1.0."""
        m = trigram_model()
        self.assertAlmostEqual(m.prob(['a', 'b'], 'c'), 2 / 3)
        self.assertAlmostEqual(m.prob(['a', 'b'], 'd'), 1 / 3)

    def test_prob_truncates_context_to_order(self):
        """A trigram model keeps at most the last n-1 = 2 context tokens.
        A longer context is truncated from the LEFT, so ['z','a','b'] is
        scored exactly like ['a','b']."""
        m = trigram_model()
        self.assertAlmostEqual(m.prob(['z', 'a', 'b'], 'c'), 2 / 3)

    def test_backoff_drops_the_oldest_context_token(self):
        """Backoff must drop the OLDEST context token and keep the most
        recent. Context ('a','c') was never seen, so we back off to ('c',)
        — NOT ('a',). ('c',) was seen once, followed by 'a': P = 1/1,
        scaled by one backoff weight 0.4, giving 0.4.

        If backoff kept ('a',) instead (the wrong end), it would find
        ('a',)->'b' and answer about 'a'-prefixed contexts entirely — a
        different, wrong subproblem."""
        # Bug 2: the recursive call must shorten the context from the LEFT
        # (drop the oldest token), not the right.
        m = trigram_model()
        self.assertAlmostEqual(m.prob(['a', 'c'], 'a'), 0.4)

    def test_backoff_scales_weight_each_step(self):
        """Each backoff step multiplies the weight by backoff_weight (0.4).
        Context ('z',) was never seen, so we back off once to the empty
        context: P('a') unigram = 4/12, scaled by 0.4 -> 0.13333..."""
        m = trigram_model()
        self.assertAlmostEqual(m.prob(['z'], 'a'), 0.4 * (4 / 12))

    def test_bigram_context_hits_directly(self):
        """The bigram context ('b',) was seen 4 times: 3x 'c', 1x 'd'. With
        a trigram model, prob(['b'], 'c') keeps the 1-token context, finds
        it directly, and returns 3/4 — no backoff."""
        m = trigram_model()
        self.assertAlmostEqual(m.prob(['b'], 'c'), 3 / 4)


class TestBackoffBase(unittest.TestCase):
    """STEP 3 — the recursion base case: the empty context.

    Backoff shortens the context one token at a time. The recursion bottoms
    out at the EMPTY context (), whose answer is the plain unigram MLE
    count(tok) / total_tokens, scaled by the accumulated weight. The base
    case is ALWAYS defined as long as anything was trained — so a token
    reached only by backing all the way down must still get a real,
    NON-ZERO probability.
    """

    def test_empty_context_returns_unigram_mle(self):
        """With the empty context, prob is the pure unigram MLE. 'c' was
        seen 3 times out of 12 total tokens, so P('c' | ()) = 3/12 = 0.25."""
        m = trigram_model()
        self.assertAlmostEqual(m.prob([], 'c'), 3 / 12)

    def test_token_reachable_only_by_full_backoff_is_nonzero(self):
        """The key base-case property. Context ('x','y') was never seen, so
        backoff goes ('x','y') -> ('y',) -> () — all the way to the unigram
        level. 'c' has unigram prob 3/12 and two backoff steps apply weight
        0.4*0.4 = 0.16, so prob = 0.16 * 0.25 = 0.04. It must NOT be 0.

        This test fails if the base case wrongly returns 0.0 — even when
        logprob's zero-floor (bug 4) is correct, because here we assert on
        `prob` directly, before any log is taken."""
        # Bug 3: the empty-context base case must return the unigram MLE,
        # not 0.0. (Pinned independently of bug 4 by asserting on prob.)
        m = trigram_model()
        self.assertAlmostEqual(m.prob(['x', 'y'], 'c'), 0.16 * (3 / 12))
        self.assertGreater(m.prob(['x', 'y'], 'c'), 0.0)

    def test_genuinely_unseen_token_is_zero(self):
        """A token that appears NOWHERE in training (not even as a unigram)
        has unigram count 0, so even the base case returns 0.0. This is the
        only legitimate way `prob` returns 0."""
        m = trigram_model()
        self.assertEqual(m.prob(['a', 'b'], 'q'), 0.0)


class TestLogprob(unittest.TestCase):
    """STEP 4 — logprob, with a finite floor for zero.

    `logprob` is log(prob). A probability of exactly 0 has no logarithm
    (log(0) = -inf), which would poison any mean it feeds into — so a zero
    probability is floored to a large finite negative number, -100.0.
    """

    def test_logprob_of_positive_prob_is_plain_log(self):
        """When prob > 0, logprob is just its natural log. P('c' | a,b) =
        2/3, so logprob = ln(2/3) = -0.405465..."""
        m = trigram_model()
        self.assertAlmostEqual(m.logprob(['a', 'b'], 'c'), math.log(2 / 3))

    def test_logprob_of_zero_is_floored_not_neg_inf(self):
        """A zero probability must be floored to a FINITE -100.0 — never
        -inf. Token 'q' is genuinely unseen, so prob is 0; logprob must be
        exactly -100.0.

        This test fails if logprob does a bare np.log(prob): np.log(0) is
        -inf. It is pinned independently of bug 3 — 'q' is unseen at EVERY
        level, so prob is legitimately 0 even with a correct base case; the
        bug being caught here is purely the missing zero-floor."""
        # Bug 4: logprob must floor a zero probability to -100.0, not let
        # np.log(0) = -inf through.
        m = trigram_model()
        lp = m.logprob(['a', 'b'], 'q')
        self.assertEqual(lp, -100.0)
        self.assertTrue(math.isfinite(lp))


class TestPerplexity(unittest.TestCase):
    """STEP 5 — perplexity of a sentence.

    Perplexity = exp(-mean logprob), each token scored against its growing
    left context. Lower means the model found the sentence less surprising.
    Because every logprob is finite (zeros floored to -100.0), perplexity
    is ALWAYS a finite number.
    """

    def test_perplexity_seen_sentence(self):
        """Perplexity of ['a','b','c'], a sentence straight from the corpus.
        Each token is scored against its growing left context:
          'a' | ()      -> 4/12
          'b' | ('a',)  -> 3/3
          'c' | ('a','b') -> 2/3
        exp(-mean(ln of those)) = 1.650963..."""
        m = trigram_model()
        self.assertAlmostEqual(m.perplexity(['a', 'b', 'c']), 1.6509636244473134)

    def test_perplexity_another_seen_sentence(self):
        """Perplexity of ['a','b','d']: same first two tokens, but 'd' |
        ('a','b') = 1/3 is rarer than 'c' was, so the sentence is more
        surprising and perplexity is higher: 2.080083..."""
        m = trigram_model()
        self.assertAlmostEqual(m.perplexity(['a', 'b', 'd']), 2.0800838230519045)

    def test_perplexity_with_unseen_token_is_finite(self):
        """A sentence containing a genuinely unseen token ('q') still gets a
        FINITE perplexity: 'q' contributes the -100.0 logprob floor, which
        makes perplexity huge but finite — never nan, never inf.

        This is the bug-3 <-> bug-4 chain end-to-end: if the base case
        returns 0 (bug 3) AND logprob lets np.log(0) through (bug 4), the
        mean becomes -inf and perplexity returns nan. Here we only require
        that the result is finite."""
        # Bug 4 (and the bug-3 chain): perplexity must stay finite even when
        # a token is unseen. nan/inf here means a -inf logprob leaked in.
        m = trigram_model()
        pp = m.perplexity(['a', 'b', 'q'])
        self.assertTrue(math.isfinite(pp))
        self.assertAlmostEqual(pp, 432039195143590.3, places=0)


class TestUtilities(unittest.TestCase):
    """STEP 6 — the utility methods.

    Small helpers, each with its own contract: prune_rare edits the counts
    table in place, token_index assigns contiguous ids, smoothed_probs
    floors a probability vector, and increase_order bumps the model order.
    """

    def test_prune_rare_drops_low_counts_in_place(self):
        """prune_rare(min_count) deletes every (context, token) entry whose
        count is below min_count, editing the table in place. With
        min_count=2, the singletons 'd' under ('b',) and ('a','b'), and the
        whole ('c',) and ('b','c') contexts (count-1 only) are emptied out.

        This must not raise: deleting from a dict while iterating it
        directly is a RuntimeError — iterate over a SNAPSHOT of the items."""
        # Bug 5: prune_rare must iterate over a copy (list(...)) of the
        # items, not mutate the dict mid-iteration.
        m = trigram_model()
        m.prune_rare(2)   # must not raise RuntimeError
        self.assertEqual(m._counts[()], {'a': 4, 'b': 4, 'c': 3})
        self.assertEqual(m._counts[('b',)], {'c': 3})
        self.assertEqual(m._counts[('a', 'b')], {'c': 2})
        self.assertEqual(m._counts[('c',)], {})

    def test_token_index_is_contiguous_and_sorted(self):
        """token_index maps each DISTINCT token to a contiguous id 0..V-1 in
        sorted order. The vocab is {'a','b','c','d'}, so the map is exactly
        {'a':0,'b':1,'c':2,'d':3}: every id 0..V-1 appears exactly once.

        This fails if the map is built from a list with duplicate tokens
        (the same token appears under many contexts): duplicate dict-comp
        keys collide, last write wins, and ids end up non-contiguous with
        max(id) >= len(map)."""
        # Bug 6: token_index must be built from the DISTINCT vocab, not a
        # flattened list of every token occurrence (whose dup keys collide).
        m = trigram_model()
        idx = m.token_index()
        self.assertEqual(idx, {'a': 0, 'b': 1, 'c': 2, 'd': 3})
        # ids are exactly 0..V-1, each once
        self.assertEqual(sorted(idx.values()), list(range(len(m.vocab))))
        self.assertEqual(max(idx.values()), len(idx) - 1)

    def test_smoothed_probs_floors_elementwise(self):
        """smoothed_probs(context) returns the probability of every vocab
        token (sorted order), floored ELEMENTWISE at 1e-6 so none is zero.

        For context ('a','b'): 'c' -> 2/3, 'd' -> 1/3 hit the trigram
        directly; 'a' and 'b' were never seen after ('a','b') so they back
        off twice to the unigram level (weight 0.16): 'a' -> 0.16*4/12,
        'b' -> 0.16*4/12. None is below 1e-6, so the floor changes nothing
        here — but the call must use np.maximum (elementwise), not np.max
        (a reduction that would raise a TypeError on the 1e-6 argument)."""
        # Bug 7: smoothed_probs must use np.maximum (elementwise floor), not
        # np.max (a reduction — treats 1e-6 as an axis arg and raises).
        m = trigram_model()
        probs = m.smoothed_probs(['a', 'b'])
        self.assertEqual(len(probs), 4)
        expected = [0.16 * (4 / 12), 0.16 * (4 / 12), 2 / 3, 1 / 3]
        for got, want in zip(probs, expected):
            self.assertAlmostEqual(float(got), want)
        self.assertTrue(all(float(p) >= 1e-6 for p in probs))

    def test_smoothed_probs_unseen_context_floors_to_1e6(self):
        """For a context whose tokens are all unseen-followers, some vocab
        tokens get a genuine 0 probability — those must be lifted to the
        1e-6 floor. token 'q'-style zeros never occur in the vocab, but a
        context like ('d',) (seen 0 times as a context) backs off: every
        vocab token still gets a positive unigram-derived value, so again
        nothing is actually clipped — the assertion is simply that the
        result is a length-4 vector with no zeros."""
        m = trigram_model()
        probs = m.smoothed_probs(['d'])
        self.assertEqual(len(probs), 4)
        self.assertTrue(all(float(p) >= 1e-6 for p in probs))

    def test_increase_order_bumps_n_immutably(self):
        """increase_order bumps the model's n-gram order by 1. NGramConfig
        is a NamedTuple — immutable — so this must REPLACE the config with
        a new one (config._replace(n=...)), not assign to config.n.

        This fails with AttributeError if it tries to mutate the NamedTuple
        field directly."""
        # Bug 8: increase_order must rebuild the config via _replace;
        # NGramConfig is an immutable NamedTuple.
        m = NGramModel(NGramConfig(n=2, backoff_weight=0.5))
        m.increase_order()
        self.assertEqual(m.config.n, 3)
        self.assertEqual(m.config.backoff_weight, 0.5)

    def test_increase_order_then_train_uses_new_order(self):
        """After increase_order, training counts one more level of k-gram.
        A model bumped from n=1 to n=2 and trained on ['a','b'] must now
        hold the bigram context ('a',) -> {'b': 1}, which an n=1 model
        would never record."""
        m = NGramModel(NGramConfig(n=1, backoff_weight=0.5))
        m.increase_order()
        m.train([['a', 'b']])
        self.assertEqual(m._counts[('a',)], {'b': 1})


if __name__ == "__main__":
    unittest.main(verbosity=2)
