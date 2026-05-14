# Mock 7 — Answer key (don't open until you've finished or are stuck)

6 root-cause bugs in `beam_search.py`. 9 of the 14 tests fail until all are fixed.
This is the **hardest mock so far**: the bugs are in *nested algorithmic logic*, the
symptom is usually far from the cause, and several bugs **interact** — three of them
(2, 3, 4) live inside the same `expand` loop and tangle together, so a single failing
end-to-end test can have up to three independent causes.

The domain: beam search over a toy bigram language model (`lm.py`). Keep `beam_width`
candidate sequences, expand each by every vocab token, score, prune to the global
top-`beam_width`, recurse. The test suite is the spec.

**Beam search in one paragraph** (for the reader who's never seen it): generating text
means picking tokens one at a time. Greedy decoding tracks one sequence and can walk
into a dead end; exhaustive search tracks all of them and is exponential. Beam search
keeps a fixed number (`beam_width`) of partial sequences — "beams" — alive at once.
Each round it *expands* every beam by every vocab token, *scores* each continuation
(a sequence's score is the **sum of its per-token log-probabilities** — log-space so
the product of many small probabilities doesn't underflow; all logprobs are negative,
so higher means more likely), *prunes* the pooled candidates down to the global
top-`beam_width`, and *recurses*. A beam that emits the EOS token is "finished" — a
complete sentence — and rides along unchanged. Search stops at `max_steps` rounds or
when every beam is finished. The final pick uses the **length-normalized** score
(`score / len(tokens)`): every extra token adds another negative logprob, so raw sums
unfairly favor short sequences — dividing by length compares them fairly. The full
narrated walkthrough is in the `beam_search.py` module docstring and the `test_*`
docstrings, ordered simplest-first.

| # | Location | Bug | Fix | Topic |
|---|----------|-----|-----|-------|
| 1 | `_step` recursive call | `return self._step(candidates, depth + 1)` — the candidate pool is fed back in **unpruned**. Each round multiplies the pool by `VOCAB_SIZE` (4), so beam search never actually narrows. | `return self._step(self.prune(candidates), depth + 1)` | recursion / algorithm structure |
| 2 | `expand` (top of method) | The finished-beam guard is **missing**. A beam that already emitted EOS gets run through `next_logprobs` and re-expanded, generating tokens *after* EOS. | re-add `if beam.finished: return [beam]` | classes / control flow |
| 3 | `expand`, score expr | `score=beam.score + logprobs[beam.tokens[-1]]` — every candidate of a beam gets the **same** increment (the parent's last-token logprob) instead of *its own* token's logprob. Pruning then can't tell a beam's children apart. | `score=beam.score + logprobs[token]` | indexing / algorithm |
| 4 | `expand`, token list | `new_tokens = beam.tokens` then `new_tokens.append(token)` — every candidate **aliases and mutates the parent's list**. All four candidates end up pointing at one list, and the parent beam is corrupted too. | `new_tokens = beam.tokens + [token]` (fresh list) | mutable aliasing / list semantics |
| 5 | `prune` | `sorted(candidates, key=lambda b: b.score)` — ascending, so prune keeps the **lowest**-scoring (least likely) candidates. Search converges on the worst sequence. | add `reverse=True` (or negate the key) | sorting / list comprehension idiom |
| 6 | `search` final selection | `max(beams, key=lambda b: b.score)` — ranks by **raw** summed logprob, so shorter sequences win unfairly (fewer negative terms summed). | `key=lambda b: b.score / len(b.tokens)` (length-normalized) | NamedTuple fields / scoring |

## How each bug shows up

- **#1** → `TestStep.test_step_never_exceeds_beam_width` — `_step` returns 64 beams instead of ≤2. Also makes every end-to-end `search` result enormous and wrong.
- **#2** → `TestExpand.test_finished_beam_returned_unchanged` — `expand` on a finished beam returns 4 post-EOS candidates instead of `[beam]`. Also drags down `test_search_end_to_end_prompt_1` / `_2`.
- **#3** → `TestExpand.test_candidate_scores_match_per_token_logprob` — all 4 candidate scores collapse to one value. Also corrupts all three end-to-end scores/sequences.
- **#4** → `TestExpand.test_candidate_token_lists_are_distinct` (all four token lists identical) and `test_expand_does_not_mutate_parent` (parent's `tokens` grew). Also corrupts all three end-to-end results.
- **#5** → `TestPrune.test_prune_keeps_highest_scoring` — keeps `-3.0` instead of `-0.5`. Also flips all three end-to-end searches to the least-likely path.
- **#6** → `TestSearch.test_search_returns_length_normalized_best` — picks the short raw-best `[0, 1]` over the length-normalized best `[0, 1, 2, 3]`.

## Debugging notes — what makes this one harder

- **Symptom far from cause.** The headline failures are the three `test_search_end_to_end_*` tests — but `search` itself only has *one* bug (#6). The other end-to-end damage is inflicted by `expand`, `prune`, and `_step`. Don't debug at the symptom; trace the intended algorithm and debug **bottom-up**: get `expand` correct, then `prune`, then `_step`, then `search`. Each layer you fix removes noise from the layer above.
- **Three bugs share one loop.** Bugs 2, 3, and 4 all live in `expand`. They were *designed* to tangle:
  - #4 (aliasing) and #3 (wrong score index) both corrupt the candidates list — if you only fix one, the `test_candidate_*` tests still fail and it's tempting to think your fix was wrong. Fix both, *then* re-run.
  - #2 (missing finished guard) is invisible until a beam actually finishes — it has *no* effect on the first `expand` call from a fresh prompt, only later in the recursion. That's why its dedicated test builds a finished beam by hand.
  - The lesson: when several tests for one function fail, fix **every** bug you can see in that function before concluding anything from a re-run.
- **Interacting bugs mask each other.** With bug #1 present (`_step` never prunes), the pool explodes — which means bug #5 (`prune` keeps the worst) is *also* in play but its symptom is buried under thousands of beams. Fixing #1 doesn't make #5's test pass; fixing #5 doesn't shrink the pool. You need both. When a fix "doesn't help," consider that a *second* bug on the same code path is still active.
- **#3 vs #4 — read the algorithm, not the line.** Both lines in `expand`'s loop *look* plausible in isolation. `logprobs[beam.tokens[-1]]` is even a valid index — it just answers the wrong question. The only way to catch these is to know what beam search is *supposed* to compute: candidate `token` should be scored by `logprobs[token]`, and each candidate needs its *own* token list. The test suite encodes exactly that intent.
- **#1 is recursion, but not the mock-1 kind.** The recursion is wired correctly (base case fine, `depth + 1` fine, return value used). The bug is a *missing transformation* on the recursive argument — `prune` was dropped. When recursion "works but the result is wrong-sized," check what's supposed to happen to the argument on the way down.
- **#6 is a one-token diff with a subtle spec.** `score` vs `score / len(tokens)`. The docstring says "LENGTH-NORMALIZED" — the test constructs a scenario where raw-score and normalized-score *disagree* so the difference is observable. Always read the docstring as part of the spec.

## Verification performed

- Buggy `beam_search.py`: **9 of 14 tests fail.**
- Reference `beam_search_solution.py`: **all 14 tests pass.**
- Mutation check — reintroducing each bug alone into the solution, every bug is caught by ≥1 test:

  | Bug | Caught by |
  |-----|-----------|
  | 1 — `_step` no prune | `test_step_never_exceeds_beam_width` |
  | 2 — `expand` no finished guard | `test_finished_beam_returned_unchanged` (+ end-to-end 1, 2) |
  | 3 — `expand` wrong-token score | `test_candidate_scores_match_per_token_logprob` (+ end-to-end 0, 1, 2) |
  | 4 — `expand` aliases token list | `test_candidate_token_lists_are_distinct`, `test_expand_does_not_mutate_parent` (+ end-to-end 0, 1, 2) |
  | 5 — `prune` ascending sort | `test_prune_keeps_highest_scoring` (+ end-to-end 0, 1, 2) |
  | 6 — `search` raw score | `test_search_returns_length_normalized_best` |
