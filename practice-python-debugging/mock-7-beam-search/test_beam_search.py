"""Spec for Mock 7 — do not edit. Fix beam_search.py until this all passes.

Run:  python -m unittest test_beam_search -v

This is the unambiguous spec for the beam-search decoder. Every expected
value below was derived by running the reference solution; they are
hardcoded so the suite does not depend on the solution file.

READING THIS FILE AS A TUTORIAL
-------------------------------
The test classes are ordered to teach beam search by example, simplest
first. Read them top to bottom:

  TestExpand — one parent beam becomes its candidate continuations:
               one candidate per vocab token, each scored by adding that
               token's logprob, EOS marks a candidate finished, and a
               beam that is already finished is passed through untouched.
  TestPrune  — many candidates pooled together, keep the top `beam_width`
               by score.
  TestStep   — one recursive round: expand all beams, prune, recurse;
               stop at `max_steps` or when every beam is finished.
  TestSearch — the whole thing: seed with the prompt, run to completion,
               pick the best finished beam by length-normalized score,
               then three full end-to-end runs.

Someone who reads only this file should come away understanding how
beam search works.
"""
import unittest

from lm import EOS_ID, VOCAB_SIZE, next_logprobs

from beam_search import Beam, BeamSearchDecoder


class TestExpand(unittest.TestCase):
    """STEP 1 — expanding one beam.

    `expand` takes a single parent beam and produces the candidate beams
    that could follow it. This is the per-beam building block of the whole
    search; `expand` is also where bugs 2, 3, and 4 all live.
    """

    def setUp(self):
        self.decoder = BeamSearchDecoder(beam_width=2, max_steps=5, eos_id=EOS_ID)

    def test_unfinished_beam_produces_one_candidate_per_token(self):
        """An unfinished beam branches into one candidate per vocab token,
        so expanding it yields exactly VOCAB_SIZE candidates."""
        beam = Beam(tokens=[0], score=0.0, finished=False)
        candidates = self.decoder.expand(beam)
        self.assertEqual(len(candidates), VOCAB_SIZE)

    def test_finished_beam_returned_unchanged(self):
        """A finished beam is already a complete sentence: expanding it
        must return just that beam, never tokens generated after EOS."""
        # Bug 2: a finished beam (already emitted EOS) must be carried
        # forward as-is — never re-expanded into post-EOS tokens.
        beam = Beam(tokens=[0, EOS_ID], score=-1.7, finished=True)
        result = self.decoder.expand(beam)
        self.assertEqual(result, [beam])

    def test_candidate_scores_match_per_token_logprob(self):
        """Scoring rule: a candidate's score is the parent's running score
        plus the logprob of the specific token that candidate appended —
        so the candidates of one parent end up with different scores."""
        # Bug 3: each candidate's score must be parent.score plus *that
        # token's* logprob — not the parent's last-token logprob applied
        # to every candidate. With the bug, all candidates share one
        # score and pruning is blind. (Use a non-zero parent score to be
        # sure the parent score is carried forward too.)
        beam = Beam(tokens=[1], score=-0.5, finished=False)
        candidates = self.decoder.expand(beam)
        scores = [c.score for c in candidates]
        # the four candidates must not all collapse to the same score
        self.assertGreater(len(set(scores)), 1)
        expected = [-0.5 + lp for lp in next_logprobs([1])]
        for got, want in zip(scores, expected):
            self.assertAlmostEqual(got, want)

    def test_candidate_token_lists_are_distinct(self):
        """Each candidate is parent.tokens + one different next token, so
        every candidate must own its own distinct token list."""
        # Bug 4: each candidate must own a fresh token list. If they alias
        # the parent's list, every candidate ends up identical (and the
        # parent gets mutated).
        beam = Beam(tokens=[0], score=0.0, finished=False)
        candidates = self.decoder.expand(beam)
        token_lists = [c.tokens for c in candidates]
        self.assertEqual(
            token_lists,
            [[0, 0], [0, 1], [0, 2], [0, 3]],
        )

    def test_expand_does_not_mutate_parent(self):
        """Expanding a beam must not mutate it: the parent stays available
        unchanged (other beams and later rounds still rely on it)."""
        # Bug 4 (other half): the parent beam's token list must be
        # untouched after expand returns.
        beam = Beam(tokens=[0], score=0.0, finished=False)
        self.decoder.expand(beam)
        self.assertEqual(beam.tokens, [0])

    def test_eos_candidate_marked_finished(self):
        """The candidate that appends EOS (token id 3) is the one — and the
        only one — marked finished; the rest are still open for extension."""
        beam = Beam(tokens=[0], score=0.0, finished=False)
        candidates = self.decoder.expand(beam)
        finished_flags = [c.finished for c in candidates]
        self.assertEqual(finished_flags, [False, False, False, True])


class TestPrune(unittest.TestCase):
    """STEP 2 — pruning the candidate pool.

    Expanding every beam produces far more candidates than we can keep.
    `prune` pools them and keeps only the `beam_width` highest-scoring —
    this is what bounds the search and is where bug 5 lives.
    """

    def setUp(self):
        self.decoder = BeamSearchDecoder(beam_width=2, max_steps=5, eos_id=EOS_ID)

    def test_prune_keeps_highest_scoring(self):
        """Pruning keeps the best-scoring candidates and drops the rest:
        with beam_width=2, the two highest scores survive."""
        # Bug 5: prune must keep the *highest* scoring candidates.
        candidates = [
            Beam(tokens=[0, 0], score=-3.0, finished=False),
            Beam(tokens=[0, 1], score=-0.5, finished=False),
            Beam(tokens=[0, 2], score=-2.0, finished=False),
        ]
        kept = self.decoder.prune(candidates)
        self.assertEqual(len(kept), 2)
        self.assertEqual({b.score for b in kept}, {-0.5, -2.0})

    def test_prune_respects_beam_width(self):
        """However many candidates go in, at most `beam_width` come out —
        that cap is what stops the search from exploding exponentially."""
        candidates = [Beam(tokens=[i], score=float(-i), finished=False) for i in range(6)]
        kept = self.decoder.prune(candidates)
        self.assertEqual(len(kept), 2)


class TestStep(unittest.TestCase):
    """STEP 3 — one recursive round.

    `_step` ties expand and prune together: expand every beam, pool the
    candidates, prune to `beam_width`, then recurse one level deeper. It
    stops at `max_steps` rounds or when every beam is finished.
    """

    def test_step_never_exceeds_beam_width(self):
        """After a round, the surviving beam set is pruned back down to at
        most `beam_width` — the width stays bounded round after round."""
        # Bug 1: each recursive round must prune back down to beam_width.
        # Without pruning the pool grows by a factor of VOCAB_SIZE/round.
        decoder = BeamSearchDecoder(beam_width=2, max_steps=3, eos_id=EOS_ID)
        beams = [Beam(tokens=[0], score=0.0, finished=False)]
        result = decoder._step(beams, 0)
        self.assertLessEqual(len(result), decoder.beam_width)

    def test_step_stops_at_max_steps(self):
        """`max_steps` is the base case: with a budget of 0 rounds, `_step`
        does no expansion and returns the beams it was given untouched."""
        decoder = BeamSearchDecoder(beam_width=2, max_steps=0, eos_id=EOS_ID)
        beams = [Beam(tokens=[0], score=0.0, finished=False)]
        result = decoder._step(beams, 0)
        self.assertEqual(result, beams)


class TestSearch(unittest.TestCase):
    """STEP 4 — the whole search.

    `search` seeds a single beam from the prompt, runs the recursive
    rounds to completion, and returns the one best beam — ranked by
    LENGTH-NORMALIZED score so short and long sequences compete fairly.
    The final three tests are complete end-to-end runs.
    """

    def test_search_returns_length_normalized_best(self):
        """The winner is chosen by score / len(tokens), not raw score:
        here the longer beam wins because its per-token average is best,
        even though its raw summed score is lower."""
        # Bug 6: search must rank final beams by score / len(tokens), not
        # raw score. Here the raw-best beam ([0, 1], -0.5) loses to the
        # length-normalized best ([0, 1, 2, 3], -0.8 -> -0.20/token).
        decoder = BeamSearchDecoder(beam_width=2, max_steps=5, eos_id=EOS_ID)
        fake_final = [
            Beam(tokens=[0, 1], score=-0.5, finished=True),
            Beam(tokens=[0, 1, 2, 3], score=-0.8, finished=True),
        ]
        decoder._step = lambda beams, depth: fake_final
        best = decoder.search([0])
        self.assertEqual(best.tokens, [0, 1, 2, 3])

    def test_search_end_to_end_prompt_0(self):
        """Full run from prompt [0]: the best sequence found is [0,1,2,3],
        a finished beam (it ends in EOS) with the expected total score."""
        decoder = BeamSearchDecoder(beam_width=2, max_steps=3, eos_id=EOS_ID)
        best = decoder.search([0])
        self.assertEqual(best.tokens, [0, 1, 2, 3])
        self.assertTrue(best.finished)
        self.assertAlmostEqual(best.score, -0.94)

    def test_search_end_to_end_prompt_1(self):
        """Full run from prompt [1] with a larger step budget: search still
        settles on the best finished sequence, [1,2,3]."""
        decoder = BeamSearchDecoder(beam_width=2, max_steps=4, eos_id=EOS_ID)
        best = decoder.search([1])
        self.assertEqual(best.tokens, [1, 2, 3])
        self.assertTrue(best.finished)
        self.assertAlmostEqual(best.score, -0.58)

    def test_search_end_to_end_prompt_2(self):
        """Full run from prompt [2] with beam_width=3: token 2's most
        likely continuation is EOS, so the best beam is the short [2,3]."""
        decoder = BeamSearchDecoder(beam_width=3, max_steps=3, eos_id=EOS_ID)
        best = decoder.search([2])
        self.assertEqual(best.tokens, [2, 3])
        self.assertTrue(best.finished)
        self.assertAlmostEqual(best.score, -0.22)


if __name__ == "__main__":
    unittest.main(verbosity=2)
