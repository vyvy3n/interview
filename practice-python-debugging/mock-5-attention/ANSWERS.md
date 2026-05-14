# Mock 5 — Answer key (don't open until you've finished or are stuck)

7 root-cause bugs in `attention.py`. 7 of the 10 tests fail until all are fixed.
This is the broadcasting + numerical-stability mock — the bugs are the ones
that actually bite in real transformer code.

| # | Location | Bug | Fix | Topic |
|---|---|---|---|---|
| 1 | `softmax` | `np.exp(x)` with no max-subtraction — for large logits, `exp` overflows to `inf`, then `inf/inf = nan`. | subtract the per-axis max first: `np.exp(x - np.max(x, axis=axis, keepdims=True))` | floating point / numerical stability |
| 2 | `softmax` | `np.sum(exp, axis=axis)` drops the reduced axis, so the divide doesn't broadcast back over a 2-D input (and silently mis-divides a square one). | `np.sum(exp, axis=axis, keepdims=True)` | broadcasting / `keepdims` |
| 3 | `scaled_dot_product_attention` | `scores = q @ k.T` is missing the `1/sqrt(head_dim)` scaling. | `scores = q @ k.T / np.sqrt(head_dim)` | floating point / spec |
| 4 | `causal_mask` | `np.tril(..., k=-1)` excludes the diagonal — every position is forbidden from attending to *itself*. | `np.tril(..., k=0)` | off-by-one in a NumPy offset |
| 5 | `apply_mask` | `np.where(mask, -np.inf, scores)` — the 3-arg branches are swapped: it sends *allowed* positions to `-inf`. | `np.where(mask, scores, -np.inf)` | `np.where` 3-arg branch order |
| 6 | `apply_padding_mask` | `pad_mask` is `(batch, seq)`; `scores` is `(batch, seq, seq)`. `np.where` can't broadcast `(batch, seq)` against `(batch, seq, seq)` — it needs a query axis inserted. | `np.where(pad_mask[:, None, :], scores, -np.inf)` | broadcasting `(B,S)` vs `(B,S,S)` |
| 7 | `count_real_tokens` | `np.sum(pad_mask, axis=0)` sums over the **batch** axis (giving a per-position count); the spec wants a per-batch-element count. | `np.sum(pad_mask, axis=1)` | `np.sum` axis |

## How each bug shows up

- **#1** → `TestSoftmax.test_large_values_stay_finite` (`nan`s in the output)
- **#2** → `TestSoftmax.test_2d_rows_sum_to_one` (`ValueError: operands could not be broadcast`)
- **#3** → `TestScaledDotProductAttention.test_matches_scaled_formula` (wrong weights — only isolated once softmax is fixed)
- **#4** → `TestCausalMask.test_diagonal_is_allowed` (`m[i, i]` is `False`)
- **#5** → `TestApplyMask.test_disallowed_positions_become_neg_inf` (`-inf` and the score are swapped)
- **#6** → `TestApplyPaddingMask.test_padding_keys_masked_for_every_query` (`ValueError` on the broadcast)
- **#7** → `TestCountRealTokens.test_per_batch_element_count` (shape `(3,)` not `(2,)`)

## Debugging notes — what makes this one hard

- **Two bugs in `softmax`, and softmax is called by `scaled_dot_product_attention`.** Fix `softmax` *first* — its own two tests (`test_large_values_stay_finite`, `test_2d_rows_sum_to_one`) guide you straight to "subtract the max" and "keepdims". Only *then* does the SDPA test isolate the missing `1/sqrt(d)` scaling (#3). Debug the leaf function before the function that calls it.
- **`nan` in a test failure almost always means numerical overflow/underflow.** The fix is nearly always the log-sum-exp trick: subtract the max before `exp`. This is *the* classic LLM-code bug.
- **A broadcasting `ValueError` names the two shapes that didn't fit.** `#2` says `(2,3)` vs `(2,)` → a missing `keepdims`. `#6` says `(2,3)` vs `(2,3,3)` → a missing `[:, None, :]` axis. The shapes in the error *are* the diagnosis.
- **`np.where` 3-arg bugs (#5):** when the output looks like the *photo-negative* of what you expect (the right values, in the wrong places), the two branches are swapped.
- **Axis bugs (#4, #7):** when an array has the right values but the wrong *shape*, or a reduction collapsed the wrong dimension, check every `axis=` and every `triu/tril` `k=`.
