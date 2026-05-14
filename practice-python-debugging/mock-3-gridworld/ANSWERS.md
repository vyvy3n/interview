# Mock 3 — Answer key (don't open until you've finished or are stuck)

6 root-cause bugs in `bandit_gridworld.py`. 8 of the 12 tests fail until all are fixed.

| # | Location | Bug | Fix | Topic |
|---|---|---|---|---|
| 1 | `Bandit.history` | `history = []` is a **class attribute** — every `Bandit` shares the same list, so pulls from one bandit show up in another's history. | Delete the class-level line; set `self.history = []` in `__init__`. | class vs instance attribute |
| 2 | `average_reward` | `sum(rewards) // len(rewards)` — floor division throws away the fractional part of the mean. | `sum(rewards) / len(rewards)` | int vs float division |
| 3 | `empirical_means` | `totals / counts` — for an arm that was never pulled, `counts` is 0, so the result is `nan` (or `inf`); the spec wants `0.0`. | `np.where(counts > 0, totals / counts, 0.0)` (or `np.divide(..., where=counts>0, out=np.zeros(num_arms))`) | `np.where`, division, floats |
| 4 | `column_totals` | `np.sum(grid, axis=1)` sums **rows**; the spec wants per-**column** sums. | `np.sum(grid, axis=0)` | `np.sum` axis |
| 5 | `GridWorld.cell_range` | `np.min(self.grid, axis=0)` returns a per-column **array**, not the scalar grid minimum. (`np.max` here is already correct — that's the contrast.) | `np.min(self.grid)` | `np.min` / `np.max` |
| 6 | `GridWorld.max_path_reward` | The recursive calls `max_path_reward(row, col+1)` and `(row+1, col)` have **no boundary guard** — at the last column/row they walk off the grid → `IndexError`. | Guard each recursive call: only recurse right if `col + 1 < n_cols`, only recurse down if `row + 1 < n_rows` (use `float("-inf")` for the unavailable direction). | recursion (missing boundary case) |

## How each bug shows up

- **#1** → `TestBandit.test_history_is_per_instance` (`first.history` ends up `[0, 1, 0]`)
- **#2** → `TestAverageReward.test_mean_of_floats`, `test_mean_is_not_floored` (`2.5` → `2.0`)
- **#3** → `TestEmpiricalMeans.test_never_pulled_arm_is_zero` (`nan != 0.0`)
- **#4** → `TestColumnTotals.test_column_sums` (`[6, 15]` instead of `[5, 7, 9]`)
- **#5** → `TestGridWorld.test_cell_range` (`int(low)` raises — `low` is an array)
- **#6** → `TestGridWorld.test_max_path_reward_2x2`, `test_max_path_reward_3x3` (`IndexError: index N is out of bounds`)

## Debugging notes

- Bug #1 is the canonical class-vs-instance trap. Tell: state from one object appears in another. `pdb`: `p Bandit.history` vs `p self.history` — if they're the *same object* (`id()` matches), that's it.
- Bug #3 prints a `RuntimeWarning: invalid value encountered in divide` to stderr before the test even fails — read your warnings, they point straight at the line.
- Bug #5 *errors* in the test (`int(low)` on an array) rather than failing a value check — the traceback line is the bug location.
- Bug #6: the `IndexError` traceback shows the exact `row, col` that went out of bounds — and the recursion that got there. A base/boundary-case bug in recursion almost always surfaces as `IndexError` or `RecursionError`.
- Note `test_max_path_reward_single_cell` (a 1×1 grid) *passes* even with bug #6, because the base case fires immediately. A test passing doesn't mean the function is correct — it means *that path* is correct.
