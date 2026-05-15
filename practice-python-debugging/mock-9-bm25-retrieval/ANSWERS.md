# Mock 9 — Answer key (don't open until you've finished or are stuck)

14 root-cause bugs across **four modules**: `tokenize_lib.py`,
`inverted_index.py`, `bm25.py`, `retrieve.py`. 26 of the 36 tests fail
(6 failures + 20 errors) until all are fixed. This is the **multi-file
interview-scale mock** — mirrors the real CodeSignal assessment: a small
codebase you've never seen, ~25 unittest tests, ~60 minutes, fix the
ROOT CAUSE of every failure.

The new difficulty axis: **symptom and cause live in different files**.
A wrong avgdl computed in `inverted_index.py` poisons every BM25 score
computed in `bm25.py` and surfaces as a wrong ranking in `retrieve.py`'s
end-to-end tests. The empty-string tokens leaked by `tokenize_lib.py`
contaminate the index in `inverted_index.py`. Don't debug at the symptom.

The domain: a BM25 retrieval pipeline. The test suite is the spec — read
it; it teaches the algorithm.

**BM25 in one paragraph** (for the reader who's never seen it): given a
query and a corpus, score every document by SUM over query terms of
`idf(term) * tf_saturation(term, doc)`. `idf` is high for rare terms and
low for terms in every doc — common words contribute little. The smoothed
form (`log((N - df + 0.5)/(df + 0.5) + 1)`) is finite at df=0 (no division
by zero on unseen terms) and non-negative at df=N (a term in every doc
gets a small positive weight, not a negative one). `tf_saturation` counts
how many times the term appears in the doc but with diminishing returns
(asymptote near `k1 + 1`), and penalises long documents via the length
norm `(1 - b + b * dl/avgdl)`. The inverted index makes this fast: for
each query term we visit only the docs that actually contain it. The
top-k step ranks by descending score with a deterministic tiebreak
(doc_id ascending). The whole pipeline is `tokenize → index → score →
top-k`.

| # | File | Location | Bug | Fix | Topic |
|---|------|----------|-----|-----|-------|
| 1 | `tokenize_lib.py` | `tokenize` | `text.lower().split(" ")` (split on the literal space) returns empty strings for runs of whitespace: `"  foo   bar  "` -> `["", "", "foo", "", "", "bar", "", ""]`. The empty strings leak into the index as a phantom term. | `text.lower().split()` (split on any-whitespace, collapses runs) — or keep `split(" ")` and filter with `if t`. | string parsing / `split()` vs `split(" ")` |
| 2 | `inverted_index.py` | `add_documents`, last line | `self._avg_doc_length = total // len(docs)` — integer division silently floors avgdl. The length-norm factor in `tf_saturation` then reads the wrong average and every score is silently wrong. | `total / len(docs)` (true division). | int vs float division |
| 4 | `inverted_index.py` | `add_documents`, top | `self._doc_freq` is never reset before re-indexing — calling `add_documents` a second time stacks the new corpus's df values on top of the first's. Stale cross-call state. | Add `self._doc_freq = {}` to the reset block. | stale state across mutations |
| 5 | `inverted_index.py` | `add_documents`, inner loop | `IndexEntry(doc.doc_id, len(tokens), tf)` — positional construction swaps `term_freq` and `doc_length` (both ints, no type error). Every BM25 saturation gets the wrong tf and the wrong dl. | Use keyword form: `IndexEntry(doc_id=doc.doc_id, term_freq=tf, doc_length=len(tokens))`. | NamedTuple positional vs keyword |
| 6 | `inverted_index.py` | `prune_rare_terms` | `for term, df in self._doc_freq.items():` then `del self._doc_freq[term]` — mutating the dict you're iterating raises `RuntimeError: dictionary changed size during iteration`. | Iterate over a snapshot: `for term, df in list(self._doc_freq.items()):`. | iterate-while-mutating |
| 15 | `inverted_index.py` | `add_documents`, for-loop body | `doc.text = doc.text.lower()` — `Document` is a NamedTuple, immutable. `AttributeError: can't set attribute`. The intent (lowercasing) is already handled inside `tokenize` — just delete the line. | Delete the line (tokenize lowercases). Alternative: `doc = doc._replace(text=doc.text.lower())`. | NamedTuple immutability |
| 7 | `bm25.py` | `idf` | `np.log(num_docs / doc_freq)` — no smoothing. `doc_freq=0` raises `ZeroDivisionError`; `doc_freq=N` returns 0 (and is borderline negative for noisy cases). | Smoothed form: `np.log((num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)`. | smoothed IDF + numerical safety |
| 8 | `bm25.py` | `tf_saturation` | `tf / (tf + k1 * length_norm)` — missing the `(k1 + 1)` factor in the numerator. The shape (monotone, length-normalised) is preserved, so rankings on simple corpora SOMETIMES survive — but the absolute scale is wrong (asymptotes at 1.0 instead of 2.2) and any test pinning the value or asymptote fails. | `(tf * (k1 + 1)) / (tf + k1 * length_norm)`. | BM25 formula |
| 9 | `bm25.py` | `score_term` | `np.where(term_idf > 0, 0.0, term_idf * term_tf_sat)` — branches swapped: returns 0 when idf is positive (every real term) and the product when idf is 0. | Just `term_idf * term_tf_sat` (both factors are non-negative; no `np.where` needed). | `np.where` branch order |
| 10 | `retrieve.py` | `top_k` | `items.sort(key=lambda dx: (dx[1], dx[0]))` — ascending score puts the WORST docs first. | `(-dx[1], dx[0])` for descending score, ascending doc_id tiebreak. | sort direction + tiebreak |
| 11 | `retrieve.py` | `top_k` | `return [d for d, s in items[:k]]` — returns bare doc_id strings, not `QueryResult` NamedTuples. Callers do `r.doc_id` / `r.score` and hit `AttributeError`. | `return [QueryResult(doc_id=d, score=s) for d, s in items[:k]]`. | return type / NamedTuple wrapping |
| 12 | `retrieve.py` | `query` | `df = index._doc_freq[term]` — direct subscript on a private dict. `KeyError` on any query term not in the index, defeating the "skip unseen terms" spec. | Use the public accessor: `df = index.doc_freq(term)` (which returns 0 on miss). | private vs public accessor / `dict[]` vs `dict.get` |
| 13 | `retrieve.py` | `parse_query`, recursive case | `return (op, [tokens[0]])` — the recursive call's accumulated terms are discarded; only the head term survives. Classic discarded-recursive-return. | `return (op, [tokens[0]] + rest_terms)` (prepend head to recursive terms). | recursion: use the recursive result |
| 14 | `retrieve.py` | `query`, accumulation | `scored[entry.doc_id] = score_term(term_idf, tf_sat)` — overwrite, not accumulate. A doc matching multiple query terms keeps only its LAST term's contribution; the sum is wrong. | `scored[entry.doc_id] = scored.get(entry.doc_id, 0.0) + score_term(...)`. | `+=` vs `=` over a dict |

(Note: bug numbers track the spec's plant list; #3 was dropped per the
spec's "drop if it can't be planted cleanly" instruction — it was the
mutable-default-argument variant which doesn't fit the InvertedIndex
API. The 14 bugs above are the full set.)

## How each bug shows up

- **#1** → `TestTokenize.test_drops_empty_tokens_from_whitespace_runs`,
  `TestEndToEnd.test_query_input_with_messy_whitespace`. The
  empty-string tokens inflate `_doc_lengths`, so any test that pins
  avg_doc_length on a whitespace-padded corpus fails.
- **#2** → `TestInvertedIndex.test_avg_doc_length_is_float_not_int`,
  `test_avg_doc_length_non_integer_corpus`. Integer division silently
  poisons every downstream score, but the type/value assertions catch
  it directly. Also nudges `test_query_input_with_messy_whitespace`.
- **#4** → `TestInvertedIndex.test_reindexing_replaces_does_not_accumulate`
  — re-indexes on a corpus with no `'the'` and asserts
  `doc_freq('the') == 0`. With stale state it's still 3.
- **#5** → `TestInvertedIndex.test_index_entry_field_names_unambiguous`,
  `test_postings_carry_term_freq_and_doc_length`, and every end-to-end
  ranking test (the swapped fields corrupt every BM25 score).
- **#6** → `TestInvertedIndex.test_prune_rare_terms_drops_low_df_in_place`
  — `RuntimeError: dictionary changed size during iteration`.
- **#15** → AttributeError cascades through every TestInvertedIndex
  and TestEndToEnd test that builds the index. Loud and obvious in the
  traceback; fix it first to clear the noise.
- **#7** → `TestBM25.test_idf_finite_at_df_zero` (ZeroDivisionError on
  unseen df=0), plus rank-corruption in end-to-end queries that mix
  rare and common terms.
- **#8** → `TestBM25.test_tf_saturation_asymptotes_near_k1_plus_one`,
  `test_tf_saturation_reference_value`. Asymptote at 1.0 instead of 2.2;
  reference `tf_saturation(1, 4, 4.0)` is ~0.45 instead of 1.0.
- **#9** → `TestBM25.test_score_term_is_idf_times_tf_saturation` —
  returns 0.0 for any positive idf instead of the product.
- **#10** → `TestRetrieve.test_top_k_descending_score`,
  `TestEndToEnd.test_single_term_query_ranks_correctly`. The single
  ascending-sort line flips the whole ranking.
- **#11** → `TestRetrieve.test_top_k_returns_query_result_namedtuples`,
  `test_top_k_tiebreak_doc_id_ascending` (the `r.doc_id` access
  AttributeErrors on a bare string). Also drags down every end-to-end
  test that does `r.doc_id`.
- **#12** → `TestRetrieve.test_query_skips_unseen_terms`,
  `TestEndToEnd.test_query_with_only_unseen_terms_returns_empty`.
  KeyError on the unseen term — the `if df == 0: continue` guard
  needs `df` from a `.get(term, 0)`-style lookup, not a hard `[term]`.
- **#13** → `TestRetrieve.test_parse_query_recursive_keeps_all_terms`,
  `test_parse_query_or_operator`. With the recursive result discarded,
  only the head term comes back.
- **#14** → `TestRetrieve.test_query_accumulates_across_multiple_terms`,
  `TestEndToEnd.test_multi_term_query_accumulates_end_to_end`. d1's
  score for `"the fox"` collapses to its `fox`-only contribution.

## Debugging notes — what makes this one harder

- **Symptom and cause live in different files.** This is the headline
  difference vs mocks 1–8. Bug #2 (int division in `inverted_index.py`)
  silently changes every score computed in `bm25.py` and surfaces only
  in end-to-end ranking tests in `retrieve.py`. Bug #1 (phantom empty
  tokens in `tokenize_lib.py`) inflates `_doc_lengths` in
  `inverted_index.py` and corrupts the length norm in `bm25.py`. When a
  test in module C fails, the bug is often in module A. **Debug
  bottom-up**: fix the tokenizer first, then the index, then the scorer,
  then the retrieval glue. Each layer fixed removes noise from the
  layer above.
- **Errors vs failures: fix the loud ones first.** Bugs #6, #11, #12,
  #15 raise exceptions (`RuntimeError`, `AttributeError`, `KeyError`,
  `AttributeError`) — they show up as `ERROR` in unittest output and
  the traceback points at the bug. Bugs #2, #5, #8, #9, #10, #14
  produce *wrong values* — they show up as `FAIL` and the symptom can
  be far away. Bug #15 in particular cascades through ~10 tests
  because it crashes during index construction; clear it first and a
  lot of red noise disappears.
- **Bug #2 vs bug #8 — two numerical bugs that mask each other.** Both
  bugs change the absolute scale of BM25 scores. With both present,
  end-to-end rankings are doubly poisoned but often in directions that
  partially cancel — fixing only one might make rankings look *worse*
  before they look better. The defence: each bug has a unit-level test
  (`test_avg_doc_length_is_float_not_int` and
  `test_tf_saturation_reference_value`) that pins it directly,
  independent of any downstream ranking. Fix at the unit level, then
  the end-to-end tests fall out.
- **Bug #7 vs bug #2 — both are numerical, but one crashes and one
  silently lies.** Bug #7 (unsmoothed idf) crashes at df=0; once you
  fix that crash, the value at df=2 might *seem* fine — but
  `test_idf_reference_value` pins the exact smoothed value, so an
  unsmoothed `log(N/df)` is also caught even when df > 0.
- **NamedTuple gotchas everywhere.** Bug #5 (positional construction
  with swapped fields, both ints — no type error), bug #11 (returning
  the wrong type entirely — bare string vs NamedTuple), and bug #15
  (attempting to mutate a NamedTuple). These three together test
  whether you remember that `NamedTuple`s are immutable AND that their
  positional-construction order matters. Use keyword form for
  construction; use the named accessors for reads.
- **"Plausible line, wrong question."** Bugs #1 (`split(" ")` vs
  `split()`), #5 (swapped fields), #13 (`[tokens[0]]` vs
  `[tokens[0]] + rest_terms`), and #14 (`=` vs `+=`) all *run without
  error* and produce *plausible-looking* values. The only way to catch
  them is to know what the algorithm is *supposed* to compute. The
  test docstrings spell out the intent — read them as part of the spec.
- **The cross-module imports are part of the spec.** Each module
  imports from the others (`retrieve` imports from all three). When
  you fix bug #15 by deleting `doc.text = doc.text.lower()`, the
  intent (lowercasing) is delegated to `tokenize` — which is itself
  buggy (#1). If you delete the lowercasing in `inverted_index` while
  `tokenize` is still buggy, indexing is now case-sensitive AND has
  phantom empty tokens. Fix the tokenizer first; then the delete is
  safe.

## Verification performed

- Buggy modules: **26 of 36 tests fail** (6 failures + 20 errors). The
  20 errors mostly trace to the cascading `AttributeError` from bug #15
  during index construction.
- Reference `*_solution.py` files: **all 36 tests pass.**
- Mutation matrix — reintroducing each bug *alone* into the solution,
  every bug is caught by ≥1 test:

  | Bug | File | Caught by |
  |-----|------|-----------|
  | 1 — `split(" ")` empty tokens | `tokenize_lib.py` | `test_drops_empty_tokens_from_whitespace_runs`, `test_query_input_with_messy_whitespace` |
  | 2 — `total // len(docs)` int div | `inverted_index.py` | `test_avg_doc_length_is_float_not_int`, `test_avg_doc_length_non_integer_corpus`, `test_query_input_with_messy_whitespace` |
  | 4 — no `_doc_freq` reset | `inverted_index.py` | `test_reindexing_replaces_does_not_accumulate` |
  | 5 — IndexEntry positional swap | `inverted_index.py` | `test_index_entry_field_names_unambiguous`, `test_postings_carry_term_freq_and_doc_length`, both ranking end-to-end tests |
  | 6 — prune iterate-while-mutating | `inverted_index.py` | `test_prune_rare_terms_drops_low_df_in_place` |
  | 7 — unsmoothed idf | `bm25.py` | `test_idf_finite_at_df_zero` (+ 3 query tests) |
  | 8 — tf_sat missing `(k1+1)` | `bm25.py` | `test_tf_saturation_asymptotes_near_k1_plus_one`, `test_tf_saturation_reference_value` (+ 4 query tests) |
  | 9 — score_term np.where swapped | `bm25.py` | `test_score_term_is_idf_times_tf_saturation` (+ end-to-end) |
  | 10 — top_k ascending sort | `retrieve.py` | `test_top_k_descending_score`, both single/two-term end-to-end |
  | 11 — top_k returns bare strings | `retrieve.py` | `test_top_k_returns_query_result_namedtuples`, every test using `.doc_id` |
  | 12 — `_doc_freq[term]` KeyError | `retrieve.py` | `test_query_skips_unseen_terms`, `test_query_with_only_unseen_terms_returns_empty` |
  | 13 — parse_query discards recursion | `retrieve.py` | `test_parse_query_recursive_keeps_all_terms`, `test_parse_query_or_operator` |
  | 14 — query overwrite not accumulate | `retrieve.py` | `test_query_accumulates_across_multiple_terms`, `test_multi_term_query_accumulates_end_to_end` |
