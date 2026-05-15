# Mock 8 — Answer key (don't open until you've finished or are stuck)

8 root-cause bugs in `ngram_model.py`. 15 of the 22 tests fail (10 failures +
5 errors) until all are fixed. This is a **gap-filler mock**: same difficulty
as mock-7 (bugs in nested logic, symptom far from cause, some bugs interact),
but it deliberately targets the bug families the other mocks under-cover —
stale cross-method state, recursion base-case / wrong-subproblem, log(0)/NaN
propagation, iterate-while-mutating, dict-comprehension key collision,
`np.max` vs `np.maximum`, and `NamedTuple` immutability.

The domain: an n-gram language model with recursive **stupid backoff**. The
test suite is the spec — read it; it teaches the algorithm.

**N-gram backoff in one paragraph** (for the reader who's never seen it): an
n-gram model predicts the next token from the previous *(n-1)* tokens — that
window is the **context**. Training is pure counting: tally how often each
context was followed by each token. The probability is the maximum-likelihood
estimate, `count(context, token) / total count for that context`. The problem:
a long context may never have appeared in training, so its counts are empty
and the estimate is 0/0. **Stupid backoff** fixes this recursively — if the
full context wasn't seen, drop the *oldest* (left-most) context token,
multiply a running `weight` by `backoff_weight` (< 1, so each backoff is
penalised), and try the shorter context. The recursion bottoms out at the
**empty context**, whose answer is the plain unigram estimate — always defined
as long as anything was trained. `logprob` is `log(prob)`, with a zero
probability floored to a finite `-100.0` so it can't poison a mean.
`perplexity` is `exp(-mean logprob)` over a sentence — always finite.

| # | Location | Bug | Fix | Topic |
|---|----------|-----|-----|-------|
| 1 | `train` | The `self._vocab = None` line is missing — re-training rebuilds `_counts` but never invalidates the lazily-cached vocab. After retraining on a new corpus, `vocab` returns the OLD token set. | Re-add `self._vocab = None` in `train`. | stale cross-method state |
| 2 | `_backoff_prob`, recursive call | `context[:-1]` drops the *newest* context token instead of the oldest — backoff keeps the wrong, stale prefix and answers a different subproblem. | `context[1:]` (drop the oldest / left-most token). | recursion on the wrong subproblem |
| 3 | `_backoff_prob`, base case | The `len(context) == 0` branch just `return 0.0` — so any token reached only by backing off all the way to the unigram level gets probability 0 instead of its real unigram estimate. | Restore the base case: look up `self._counts[()]`, return `weight * count / total`. | recursion base case |
| 4 | `logprob` | `return float(np.log(self.prob(...)))` — no zero-floor. A zero probability → `np.log(0)` → `-inf` → `perplexity` averages in `-inf` → returns `nan`. | `p = self.prob(...); return float(np.log(p)) if p > 0 else -100.0` | log(0) + NaN propagation |
| 5 | `prune_rare` | `for token, count in ctx_counts.items()` then `del ctx_counts[token]` — mutating the dict while iterating it raises `RuntimeError: dictionary changed size during iteration`. | Iterate over a snapshot: `list(ctx_counts.items())`. | iterate-while-mutating |
| 6 | `token_index` | Builds the map from `all_tokens = [tok for ctx in self._counts.values() for tok in ctx]` — a flattened list with the same token repeated across contexts. The dict-comp's duplicate keys collide (last write wins), so ids are non-contiguous and `max(id) >= len(map)`. | `{tok: i for i, tok in enumerate(sorted(self.vocab))}` — build from the *distinct* vocab. | nested comprehension + dict-comp key collision |
| 7 | `smoothed_probs` | `np.max(probs, 1e-6)` — `np.max` is a *reduction*; it reads `1e-6` as the `axis` argument and raises `TypeError`. The intent is an *elementwise* floor. | `np.maximum(probs, 1e-6)` (elementwise). | reduction vs elementwise |
| 8 | `increase_order` | `self.config.n += 1` — `NGramConfig` is a `NamedTuple`, immutable; this raises `AttributeError: can't set attribute`. | `self.config = self.config._replace(n=self.config.n + 1)` | NamedTuple immutability |

## How each bug shows up

- **#1** → `TestTraining.test_retrain_refreshes_vocab_cache` — trains, reads `vocab` (caches it), retrains on a fresh corpus, asserts `vocab` reflects only the new corpus. With the bug it returns the stale cached set.
- **#2** → `TestProbBackoff.test_backoff_drops_the_oldest_context_token` — context `('a','c')` was never seen; correct backoff goes to `('c',)` and finds `('c',)->'a'`. With `context[:-1]` it backs off to `('a',)` instead — a different subproblem — and gets the wrong probability. Also corrupts `test_smoothed_probs_floors_elementwise` (a backed-off probability changes).
- **#3** → `TestBackoffBase.test_empty_context_returns_unigram_mle`, `test_token_reachable_only_by_full_backoff_is_nonzero`, `test_backoff_scales_weight_each_step`, and all three `TestPerplexity` tests (the zeros it produces propagate). The 0.0 base case poisons everything that ever backs off to the unigram level.
- **#4** → `TestLogprob.test_logprob_of_zero_is_floored_not_neg_inf` (a genuinely-unseen token's `logprob` must be the finite `-100.0`, not `-inf`) and `TestPerplexity.test_perplexity_with_unseen_token_is_finite` (the `-inf` makes the mean `-inf`, so `perplexity` returns `nan`).
- **#5** → `TestUtilities.test_prune_rare_drops_low_counts_in_place` — `prune_rare(2)` raises `RuntimeError` mid-iteration.
- **#6** → `TestUtilities.test_token_index_is_contiguous_and_sorted` — the id map is non-contiguous; `max(id)` exceeds `len(map) - 1`.
- **#7** → `TestUtilities.test_smoothed_probs_floors_elementwise` and `test_smoothed_probs_unseen_context_floors_to_1e6` — `np.max` raises `TypeError` before any value comes back.
- **#8** → `TestUtilities.test_increase_order_bumps_n_immutably` and `test_increase_order_then_train_uses_new_order` — `AttributeError` on the assignment.

## Debugging notes — what makes this one harder

- **Symptom far from cause.** The loudest failures are the three `TestPerplexity`
  tests, but `perplexity` itself has **no bug**. Trace the chain backwards:
  `perplexity` returns `nan` ← `np.mean` of a list containing `-inf` ← `logprob`
  returned `-inf` ← `np.log(0)` ← `prob` returned `0` ← the `_backoff_prob` base
  case returned `0.0`. The fix is two methods upstream of the symptom (bugs 3
  and 4). Don't debug at the symptom — debug **bottom-up**: get `prob` /
  `_backoff_prob` correct first, then `logprob`, then `perplexity` falls out.
- **The bug-3 ↔ bug-4 chain — and why each still has its own test.** Bugs 3 and
  4 are designed to tangle: bug 3 manufactures the zero probabilities, bug 4
  turns those zeros into `-inf`. Together they make `perplexity` return `nan`.
  But each is pinned **independently**:
  - **Bug 3** is caught by `test_token_reachable_only_by_full_backoff_is_nonzero`,
    which asserts on `prob` *directly* — `prob(['x','y'],'c')` must be the
    nonzero unigram-derived `0.04`. No `log` is taken, so fixing bug 4 cannot
    rescue this test; only fixing the base case does.
  - **Bug 4** is caught by `test_logprob_of_zero_is_floored_not_neg_inf`, which
    uses token `'q'` — a token that appears **nowhere** in training. Its
    probability is *legitimately* `0` even with a perfectly correct base case,
    so fixing bug 3 cannot rescue this test; only adding the zero-floor does.
  - The lesson: when two bugs share a failure (`perplexity` → `nan`), find the
    test that isolates *each* — the one that fails with the other bug already
    fixed. That tells you you genuinely have two distinct root causes.
- **Stale state looks like a bug in the wrong file.** Bug 1's symptom appears
  in the `vocab` property — but `vocab` is correct. The cache-read is fine; the
  missing **cache invalidation** is in `train`. When cached state is wrong,
  check every writer of the underlying data, not the reader.
- **"Plausible line, wrong question."** Bug 2 (`context[:-1]`) and bug 6
  (`all_tokens` flatten) both *run without error* and produce *plausible-looking*
  values. `context[:-1]` is a perfectly valid slice — it just drops the wrong
  end. The flattened token list is a perfectly valid list — it just has
  duplicates that collide as dict keys. The only way to catch these is to know
  what the algorithm is *supposed* to compute. The test docstrings spell out
  the intent: backoff drops the *oldest* token; `token_index` maps the
  *distinct* vocab.
- **Errors vs failures.** Bugs 5, 7, 8 raise exceptions (`RuntimeError`,
  `TypeError`, `AttributeError`) — they show up as `ERROR`, not `FAIL`, and the
  traceback points almost exactly at the bug. Bugs 1–4, 6 produce *wrong values*
  — they show up as `FAIL` and the symptom can be far away. Fix the loud
  `ERROR`s first to clear noise, then chase the quiet `FAIL`s bottom-up.

## Verification performed

- Buggy `ngram_model.py`: **15 of 22 tests fail** (10 failures + 5 errors).
- Reference `ngram_model_solution.py`: **all 22 tests pass.**
- Mutation matrix — reintroducing each bug *alone* into the solution, every bug
  is caught by ≥1 test:

  | Bug | Caught by |
  |-----|-----------|
  | 1 — `train` no vocab invalidation | `test_retrain_refreshes_vocab_cache` |
  | 2 — `_backoff_prob` drops wrong end | `test_backoff_drops_the_oldest_context_token` (+ `test_smoothed_probs_floors_elementwise`) |
  | 3 — `_backoff_prob` base case `0.0` | `test_token_reachable_only_by_full_backoff_is_nonzero`, `test_empty_context_returns_unigram_mle`, `test_backoff_scales_weight_each_step`, all 3 `TestPerplexity` tests, `test_smoothed_probs_floors_elementwise` |
  | 4 — `logprob` no zero-floor | `test_logprob_of_zero_is_floored_not_neg_inf`, `test_perplexity_with_unseen_token_is_finite` |
  | 5 — `prune_rare` mutate-while-iterate | `test_prune_rare_drops_low_counts_in_place` |
  | 6 — `token_index` dup-key collision | `test_token_index_is_contiguous_and_sorted` |
  | 7 — `smoothed_probs` `np.max` | `test_smoothed_probs_floors_elementwise`, `test_smoothed_probs_unseen_context_floors_to_1e6` |
  | 8 — `increase_order` mutates NamedTuple | `test_increase_order_bumps_n_immutably`, `test_increase_order_then_train_uses_new_order` |
