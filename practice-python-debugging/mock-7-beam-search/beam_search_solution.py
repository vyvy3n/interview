"""Mock 7 — Beam-search decoder (LLM domain). [HARD] — REFERENCE SOLUTION.

This is the clean, correct implementation. `beam_search.py` is this file
with 6 bugs planted. Use this to derive expected values.
"""
from typing import NamedTuple

from lm import next_logprobs


class Beam(NamedTuple):
    tokens: list      # token ids so far (including the prompt)
    score: float      # sum of per-token logprobs
    finished: bool    # True once EOS has been emitted


class BeamSearchDecoder:
    def __init__(self, beam_width, max_steps, eos_id):
        self.beam_width = beam_width
        self.max_steps = max_steps
        self.eos_id = eos_id

    def expand(self, beam):
        """Candidate beams produced from `beam`. A finished beam is carried
        forward unchanged. An unfinished beam produces one candidate per
        vocab token: score = parent score + that token's logprob; the
        candidate is finished iff the token is EOS."""
        if beam.finished:
            return [beam]
        logprobs = next_logprobs(beam.tokens)
        candidates = []
        for token in range(len(logprobs)):
            new_tokens = beam.tokens + [token]
            candidates.append(Beam(
                tokens=new_tokens,
                score=beam.score + logprobs[token],
                finished=(token == self.eos_id),
            ))
        return candidates

    def prune(self, candidates):
        """Keep the `beam_width` highest-scoring candidates."""
        return sorted(candidates, key=lambda b: b.score, reverse=True)[: self.beam_width]

    def _step(self, beams, depth):
        """One recursive beam-search round."""
        if depth >= self.max_steps or all(b.finished for b in beams):
            return beams
        candidates = []
        for beam in beams:
            candidates.extend(self.expand(beam))
        return self._step(self.prune(candidates), depth + 1)

    def search(self, prompt):
        """Beam search from `prompt` (a sequence of token ids). Returns the
        single best beam by LENGTH-NORMALIZED score (score / len(tokens))."""
        beams = [Beam(tokens=list(prompt), score=0.0, finished=False)]
        beams = self._step(beams, 0)
        return max(beams, key=lambda b: b.score / len(b.tokens))
