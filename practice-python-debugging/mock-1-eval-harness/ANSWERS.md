# Mock 1 — Answer key (don't open until you've finished or are stuck)

7 root-cause bugs in `eval_harness.py`. 13 of the 16 tests fail until all are fixed.

| # | Location | Bug | Fix | Topic |
|---|---|---|---|---|
| 1 | `make_config` | `EvalConfig(num_samples, num_classes, seed)` — positional args in the wrong order, so `num_classes`/`num_samples` are swapped. | `EvalConfig(num_classes, num_samples, seed)` | NamedTuple field order |
| 2 | `LabelSampler.sample` | Uses the **global** `np.random.randint`, not `self.rng`. Not reproducible; global `np.random.seed` leaks in. | `self.rng.randint(...)` | `np.random.RandomState` |
| 3 | `LabelStats.from_labels` | `np.bincount(labels)` returns length `labels.max()+1`, which is too short when the top class is absent. | `np.bincount(labels, minlength=num_classes)` | `np.bincount` |
| 4 | `LabelStats.fractions` | Divides by `num_classes` instead of the total count, so it doesn't sum to 1. | `self.counts / self.counts.sum()` | floats / `np.sum` |
| 5 | `per_sample_totals` | `np.sum(matrix, axis=0)` sums **columns**; the spec wants per-row sums. | `np.sum(matrix, axis=1)` | `np.sum` axis |
| 6 | `passing_indices` | `np.where(cond)` (1-arg) returns a **tuple** of index arrays, not a 1-D array. | `np.where(scores > threshold)[0]` | `np.where` / `np.nonzero` |
| 7 | `flatten_scores` | The recursive call `flatten_scores(item)` discards its return value, so nested elements vanish. | `flat.extend(flatten_scores(item))` | recursion (propagate return value) |

## How each bug shows up

- **#1** → `TestMakeConfig.test_fields_assigned_by_name`
- **#2** → `TestLabelSampler.test_reproducible_across_instances`, `test_isolated_from_global_rng`
- **#3** → `TestLabelStats.test_counts_shape_when_top_class_absent`, `test_counts_values`
- **#4** → `TestLabelStats.test_fractions_sum_to_one`, `test_fractions_values`
- **#5** → `TestPerSampleTotals.test_row_sums`, `test_single_row`
- **#6** → `TestPassingIndices.*` (raises `AttributeError: 'tuple' has no attribute 'ndim'`)
- **#7** → `TestFlattenScores.test_nested`, `test_deeply_nested`

## Debugging notes

- Bug #2 is the kind where the test name tells you everything: "reproducible" + "isolated from global rng" → look for global RNG use. `pdb`: break in `sample()`, `p self.rng` vs what's actually called.
- Bug #3: the failure is a **shape** mismatch, not a value mismatch — that's the tell for a `bincount`/reshape/broadcasting issue.
- Bug #6 errors rather than fails — read the traceback: `'tuple' object has no attribute 'ndim'` points straight at the 1-arg `np.where` returning a tuple.
- Bug #7: classic "recursion returns None / drops branches." Print `flat` at each level, or `pdb` step into the recursive call and watch the result get thrown away.
