# Mock 2 — Answer key (don't open until you've finished or are stuck)

6 root-cause bugs in `token_analyzer.py`. 10 of the 13 tests fail until all are fixed.

| # | Location | Bug | Fix | Topic |
|---|---|---|---|---|
| 1 | `Vocab.encode` | List comprehension has no filter — `self.token_to_id[tok]` raises `KeyError` on a token not in the vocab, but the spec says unknown tokens are skipped. | add `if tok in self.token_to_id` to the comprehension | list comprehension (missing filter) |
| 2 | `token_counts` | `np.bincount(ids)` returns length `ids.max()+1`, too short when the document doesn't use the highest token id. | `np.bincount(ids, minlength=len(vocab.tokens))` | `np.bincount` |
| 3 | `high_frequency_ids` | Uses the **3-arg** `np.where(cond, counts, 0)` (elementwise *select*), but the spec wants the **indices** where the condition holds. | `np.where(counts > threshold)[0]` | `np.where` 1-arg vs 3-arg |
| 4 | `normalize_rows` | `matrix / row_sums` — `row_sums` has shape `(num_docs,)`; dividing `(num_docs, vocab_size)` by `(num_docs,)` fails to broadcast (trailing dims `vocab_size` vs `num_docs`). | `matrix / row_sums[:, None]` | broadcasting `(n,)` vs `(n,1)` |
| 5 | `cooccurrence` | `doc_a > 0 and doc_b > 0` — Python `and` on two arrays raises `ValueError: truth value of an array is ambiguous`. | `(doc_a > 0) & (doc_b > 0)` | NumPy boolean ops |
| 6 | `merge_vocabs` | Mutable default argument `seen=[]` — the same list is reused across calls, so results leak between invocations. | `seen=None` + `if seen is None: seen = []` | mutable default argument |

## How each bug shows up

- **#1** → `TestVocab.test_encode_skips_unknown_tokens` (raises `KeyError: 'q'`)
- **#2** → `TestTokenCounts.test_counts_full_length` (shape `(2,)` ≠ `(4,)`)
- **#3** → `TestHighFrequencyIds.*` (returns selected values, not indices)
- **#4** → `TestNormalizeRows.test_rows_sum_to_one`, `test_values` (raises `ValueError: operands could not be broadcast`)
- **#5** → `TestCooccurrence.*` (raises `ValueError: ambiguous truth value`)
- **#6** → `TestMergeVocabs.test_independent_across_calls` fails; `test_merges_in_first_appearance_order` may pass or fail depending on test order (the classic mutable-default tell — passes alone, fails in a suite)

## Debugging notes

- Bugs #4 and #5 **raise** rather than fail — read the traceback. "could not be broadcast together with shapes (2,3) (2,)" → a `(n,)` vs `(n,1)` shape bug. "truth value of an array … is ambiguous" → `and`/`or` used where `&`/`|` is needed.
- Bug #6 is the canonical "passes in isolation, fails in a suite" symptom. If you see a test that only fails when run after another test, suspect shared mutable state — a mutable default arg or a class attribute.
- Bug #3: when a `np.where` result has the *same shape and dtype as the input* instead of being a short index array, you're on the 3-arg form by mistake.
