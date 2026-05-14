# Mock 4 — Answer key (don't open until you've finished or are stuck)

7 root-cause bugs in `bpe_tokenizer.py`. 10 of the 13 tests fail until all are fixed.
Harder than mocks 1–3: the recursion bug is an off-by-one in the *loop range* (not a discarded return), and several bugs are in helpers used by multiple call sites.

| # | Location | Bug | Fix | Topic |
|---|---|---|---|---|
| 1 | `build_vocab` | `ranked[: config.vocab_size]` keeps `vocab_size` *characters* — but `vocab_size` is the total **including** the 2 special tokens, so the vocab ends up 2 too long. | `ranked[: config.vocab_size - _NUM_SPECIAL]` | off-by-one / spec reading |
| 2 | `build_vocab` return | `Vocab(id_to_token, token_to_id, _PAD_ID, _UNK_ID)` — the last two positional args are `unk_id, pad_id` in the NamedTuple definition, but they're passed **swapped**. `vocab.unk_id` becomes 1, `vocab.pad_id` becomes 0. | `Vocab(id_to_token, token_to_id, _UNK_ID, _PAD_ID)` | NamedTuple positional order |
| 3 | `apply_merges` | `range(len(tokens) - 2)` — the last valid adjacent-pair index is `len(tokens) - 2`, and `range` is exclusive, so the **last pair is never checked**. Merges that should happen at the end of the list are silently skipped. | `range(len(tokens) - 1)` | recursion / loop range off-by-one |
| 4 | `BPETokenizer.encode` | `self.vocab.token_to_id[tok]` raises `KeyError` for a token not in the vocab; the spec says unknown tokens map to `unk_id`. | `self.vocab.token_to_id.get(tok, self.vocab.unk_id)` | list comprehension / `dict.get` |
| 5 | `token_frequencies` | `np.bincount(np.array(all_ids))` returns length `max(id)+1` — too short when high-id tokens never appear. | `np.bincount(np.array(all_ids), minlength=vocab_size)` | `np.bincount` minlength |
| 6 | `non_pad_length` | `np.where(ids != pad_id)` returns a **tuple** of index arrays; `len(tuple)` is always 1. | `return int(np.sum(ids != pad_id))` (or `len(np.where(ids != pad_id)[0])`) | `np.where` / `np.nonzero` |
| 7 | `compression_ratio` | `len(text) // len(ids)` — floor division throws away the fractional part of the ratio. | `len(text) / len(ids)` | floating point / division |

## How each bug shows up

- **#1** → `TestBuildVocab.test_vocab_size_includes_specials` (`len` is 7, not 5)
- **#2** → `TestBuildVocab.test_special_token_ids` (`unk_id` is 1, not 0)
- **#3** → `TestApplyMerges.test_merges_including_last_pair`, `test_merge_at_nonzero_index`; also `TestEncodeDecode.test_encode_applies_all_merges`
- **#4** → `TestEncodeDecode.test_encode_unknown_char_maps_to_unk` (`KeyError: 'z'`)
- **#5** → `TestTokenFrequencies.test_frequencies_cover_full_vocab` (shape `(5,)` not `(7,)`)
- **#6** → `TestNonPadLength.test_counts_non_pad`, `test_all_pad` (always returns 1)
- **#7** → `TestCompressionRatio.test_ratio_is_fractional` (`2` instead of `2.5`)

## Debugging notes — what makes this one harder

- **Bug #3 is the headline.** It's recursion, but the bug isn't "the return value is discarded" (mock-1). The recursion is wired correctly — the bug is the **loop range** inside it misses the last pair. Symptom: `apply_merges` *sometimes* works (when merges are mid-list) and sometimes leaves the tail unmerged. When a bug is intermittent-by-position, suspect a range/boundary off-by-one. `pdb`: break in `apply_merges`, `p list(range(len(tokens)-2))` vs the indices you actually need.
- **Bugs in shared helpers cascade.** `apply_merges` (#3) is called by `encode`, so a failing `encode` test might be `encode`'s fault *or* `apply_merges`'s. Fix the leaf helper first, re-run, then see what's still red. Always debug bottom-up.
- **Bug #1 vs #2 both live in `build_vocab`** but each has its own isolated test — #1's test only checks length, #2's only checks the special ids. When two bugs share a function, look for which *specific assertion* fails to tell them apart.
- **Bug #4 errors, the rest fail.** `KeyError` in the traceback points straight at a bare `dict[key]` that should be `dict.get(key, default)` — the spec ("unknown tokens map to unk_id") tells you the default.
