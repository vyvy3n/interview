"""Mock 7 — Beam-search decoder (LLM domain). [HARD]

WHAT IS BEAM SEARCH?
--------------------
A language model, given a sequence of tokens, predicts a probability for
every possible next token. To *generate* text you have to pick tokens one
after another. Greedy decoding just takes the single most-likely token at
each step — but a token that looks best right now can lead into a dead end,
so greedy often misses the best overall sequence.

Beam search is the compromise between greedy (track 1 option) and an
exhaustive search (track every option — exponential, infeasible). It keeps
a fixed number of partial sequences alive at once. Each partial sequence is
called a "beam". `beam_width` is how many beams we keep.

THE LOOP (expand -> score -> prune -> recurse):
  1. EXPAND: for every beam, try every vocab token as the next token. A
     beam of width-many parents with a vocab of size V produces up to
     beam_width * V candidate continuations.
  2. SCORE: each candidate gets a score (see "scores" below).
  3. PRUNE: pool ALL candidates from ALL beams together and keep only the
     global top-`beam_width`. This is the key step — beams compete with
     each other, so a weak beam can be dropped entirely and a strong beam
     can spawn several survivors.
  4. RECURSE: repeat with the surviving beams as the new parents.

SCORES ARE SUMMED LOG-PROBABILITIES:
The probability of a whole sequence is the product of its per-token
probabilities. Multiplying many small probabilities underflows toward
zero, so we work in log space: log(a*b) = log(a)+log(b), so a sequence's
score is the SUM of per-token log-probabilities. Every logprob is
negative (log of a number < 1), so scores are negative and HIGHER (closer
to 0) means MORE likely.

"FINISHED" / EOS:
The vocabulary contains a special end-of-sequence token (`eos_id`). Once a
beam emits EOS it is "finished" — it represents a complete sentence and
must not grow any further. Finished beams are carried forward unchanged
through every later round so they can still compete in pruning.

`max_steps`:
An upper bound on how many expansion rounds run, so search always
terminates even if some beam never emits EOS.

LENGTH NORMALIZATION:
Every extra token adds another negative logprob, so a longer sequence
almost always has a lower (worse-looking) raw score than a short one —
even when it is the better sentence. To compare sequences of different
lengths fairly, the final pick divides each beam's score by its length
(score / len(tokens)) — the average per-token logprob — instead of using
the raw sum.

---
This module has bugs. The unittest suite in `test_beam_search.py` is the
spec — fix the root cause of every failure so the whole suite passes. Do
not edit the test file or lm.py. Don't worry about behavior the tests
don't check.
"""
from typing import NamedTuple

from lm import next_logprobs


class Beam(NamedTuple):
    """One partial (or completed) candidate sequence in the search.

    tokens   — the token ids chosen so far, including the prompt.
    score    — running sum of per-token logprobs (negative; higher = better).
    finished — True once this beam has emitted EOS; a finished beam is a
               complete sentence and is never extended again.
    """
    tokens: list      # token ids so far (including the prompt)
    score: float      # sum of per-token logprobs
    finished: bool    # True once EOS has been emitted


class BeamSearchDecoder:
    def __init__(self, beam_width, max_steps, eos_id):
        self.beam_width = beam_width   # how many beams survive each prune
        self.max_steps = max_steps     # hard cap on expansion rounds
        self.eos_id = eos_id           # the end-of-sequence token id

    def expand(self, beam):
        """Produce the candidate beams that follow from one parent `beam`.

        A finished beam is already a complete sentence, so it is carried
        forward unchanged (exactly one candidate: itself). An unfinished
        beam produces one candidate per vocabulary token: the candidate's
        tokens are the parent's tokens plus that token, its score is the
        parent's score plus that token's logprob, and it is marked
        finished iff the token it just appended is EOS.
        """
        logprobs = next_logprobs(beam.tokens)   # logprob of each possible next token
        candidates = []
        for token in range(len(logprobs)):
            # each candidate continues the parent by exactly one token
            new_tokens = beam.tokens
            new_tokens.append(token)
            candidates.append(Beam(
                tokens=new_tokens,
                # extend the running score by this token's own logprob
                score=beam.score + logprobs[beam.tokens[-1]],
                # the sentence ends exactly when EOS is appended
                finished=(token == self.eos_id),
            ))
        return candidates

    def prune(self, candidates):
        """Keep only the `beam_width` highest-scoring candidates.

        `candidates` is the pooled list of continuations from ALL parent
        beams of this round — they compete globally, not within their own
        parent — so this is what actually bounds the search width.
        """
        return sorted(candidates, key=lambda b: b.score)[: self.beam_width]

    def _step(self, beams, depth):
        """Run one recursive round of beam search.

        Base case: stop and return the current beams once `max_steps`
        rounds have run, or once every beam is finished (all sentences
        complete — nothing left to extend). Otherwise expand every beam,
        pool the candidates, prune to `beam_width`, and recurse one level
        deeper.
        """
        if depth >= self.max_steps or all(b.finished for b in beams):
            return beams
        candidates = []
        for beam in beams:
            # pool continuations from every beam so they compete globally
            candidates.extend(self.expand(beam))
        return self._step(candidates, depth + 1)

    def search(self, prompt):
        """Run beam search from `prompt` (a list of token ids).

        Seed the search with a single unfinished beam holding just the
        prompt (score 0.0 — no tokens generated yet), run the recursive
        rounds, then return the single best surviving beam. "Best" is by
        LENGTH-NORMALIZED score (score / len(tokens)) so short and long
        sequences are compared fairly.
        """
        beams = [Beam(tokens=list(prompt), score=0.0, finished=False)]
        beams = self._step(beams, 0)
        return max(beams, key=lambda b: b.score)
