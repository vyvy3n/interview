# Mock 6 — Answer key (don't open until you've finished or are stuck)

8 root-cause bugs in `sampler.py`. 11 of the 15 tests fail until all are fixed.
This is the hardest mock: 8 bugs, every one a distinct archetype, all in the
decoding stack that turns logits into generated tokens.

| # | Location | Bug | Fix | Topic |
|---|---|---|---|---|
| 1 | `apply_temperature` | `logits * temperature` — temperature *divides* logits (higher temp ⇒ flatter). Multiplying does the opposite. | `logits / temperature` | formula / floating point |
| 2 | `top_k_filter` | `np.argsort(probs)[:k]` takes the k **lowest**-probability ids (argsort is ascending). | `np.argsort(probs)[-k:]` | `np.argsort` direction |
| 3 | `top_p_filter` | The nucleus is selected correctly, but the result is returned **without renormalizing** — it doesn't sum to 1.0. | `return filtered / filtered.sum()` | floating point / renormalization |
| 4 | `greedy_next_token` | `np.max(probs)` returns the highest *probability value*; greedy decoding needs the *id*. | `int(np.argmax(probs))` | `np.max` vs `np.argmax` |
| 5 | `surviving_token_ids` | `np.nonzero(probs)` returns a **tuple** of index arrays, not a 1-D array. | `np.nonzero(probs)[0]` | `np.nonzero` |
| 6 | `Sampler.sample` | `rng = np.random.RandomState(self.seed)` re-seeds a fresh RNG **on every call**, so every draw is identical — the stream never advances. | use the instance RNG: `self.rng.choice(...)` | `np.random.RandomState` |
| 7 | `generate` | base case `if len(prompt) > max_length` stops one step too late — it returns a sequence of length `max_length + 1`. | `if len(prompt) >= max_length` | recursion base-case off-by-one |
| 8 | `perplexity` | `np.exp(mean_logprob)` is missing the negation; perplexity is `exp(-mean_logprob)`. | `np.exp(-mean_logprob)` | floating point / formula |

## How each bug shows up

- **#1** → `TestApplyTemperature.test_high_temperature_shrinks_logits`
- **#2** → `TestTopKFilter.test_keeps_the_k_highest`
- **#3** → `TestTopPFilter.test_result_is_renormalized`
- **#4** → `TestGreedyNextToken.test_returns_argmax_id` (returns `0.6`, expected id `1`)
- **#5** → `TestSurvivingTokenIds.test_returns_1d_id_array` (`'tuple' has no attribute 'ndim'`)
- **#6** → `TestSampler.test_draws_advance_the_stream` (all 20 draws identical), `test_reproducible_across_samplers`
- **#7** → `TestGenerate.test_generates_exactly_max_length` (length 5, not 4), `test_prompt_already_at_length`
- **#8** → `TestPerplexity.test_uniform_two_way_distribution` (`0.5` instead of `2.0`)

## Debugging notes — what makes this one hardest

- **8 bugs, 8 archetypes, ~110 lines.** Under a 60-min clock you can't afford to *read* your way through — run the suite, let each failure name a function, and triage. The most-failing functions first.
- **`test_returns_an_integer_id` passes even with bug #4.** `int(np.max([0.7,0.2,0.1]))` is `int(0.7)` = `0`, which happens to equal the argmax id here. A test passing does **not** mean the function is right — `test_returns_argmax_id` (a non-coincidental case) is the one that catches it. When two tests cover one function and only one fails, trust the failing one.
- **Bug #6 — "all draws identical" — means the RNG isn't advancing.** Two suspects: re-seeding inside the hot path (this bug), or using the global `np.random` instead of an instance RNG. `pdb`: break in `sample`, `p self.rng` and check whether a *fresh* RandomState is being made each call.
- **Bug #7 — recursion off-by-one — surfaces as a length that's wrong by exactly 1.** When a recursive function's output is one element too long/short, the base-case comparison is almost always `>` vs `>=` (or `<` vs `<=`). Trace the last two recursive calls by hand.
- **Bugs #1 and #8 are formula errors** — the code runs fine and returns a plausible-looking number that's just *wrong*. These are the ones print-debugging catches fastest: print the intermediate value, compare to what you'd compute by hand for the test's input.
- **Bug #3 — "doesn't sum to 1"** — any time a probability-distribution function fails a `.sum() == 1` check, look for a missing `/ x.sum()` after a filtering/zeroing step.
