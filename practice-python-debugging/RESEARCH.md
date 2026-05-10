# Anthropic Fellows — 60-Minute Python Debugging CodeSignal (Constellation)
## Research outline & prep plan

> **Honesty disclaimer up front:** The 60-minute *Python debugging* CodeSignal
> described in your official email is **not directly attested anywhere I could
> find on the public web**. Every public candidate writeup I located covers the
> 90-minute *general* CodeSignal (the in-memory database / bank-account /
> banking-system progressive build), the live coding round, the take-home, or
> the final research brainstorm. There are *no* public Reddit threads, Blind
> threads, Medium posts, Glassdoor entries, or interviewing.io guides that
> describe the specific assessment your email references. Treat this outline
> accordingly: the **format and required-knowledge list comes only from your
> email itself**, and everything else here is either (a) cross-checked against
> CodeSignal's documented "Bugfix" / "Debugging Code Using Python" formats or
> (b) inferred from the explicit topic list (NamedTuple, bincount, where,
> RandomState, broadcasting, pdb).

---

## 1. What the test actually looks like

### 1.1 Directly attested (your email)

- **60 minutes**, proctored via CodeSignal / Constellation.
- Format: an **existing codebase** is provided with a **failing `unittest`
  suite**. The candidate's job is to **fix the root cause(s)** so the tests
  pass. This is *not* the 4-level progressive-build format used in the 90-min
  general CodeSignal.
- Operating instruction: **"In case of ambiguity, use the provided test suite
  as the final word on the requirements. Don't worry about edge cases if
  there are no tests checking them."** This is critical: it explicitly
  inverts the usual Anthropic "edge cases matter" advice from public guides
  ([Sundeep Teki](https://www.sundeepteki.org/advice/anthropic-codesignal-assessment-guide),
  [interviewing.io](https://interviewing.io/anthropic-interview-questions)) —
  in this test, *only what the tests exercise* matters.
- **Required Python knowledge** (verbatim from the email): classes, methods,
  list comprehensions, recursion, `collections.NamedTuple` (their wording —
  but note: in actual Python, `NamedTuple` lives in `typing`; `namedtuple` is
  in `collections`. The email is almost certainly referring to
  `typing.NamedTuple`.), `unittest`.
- **Required NumPy knowledge** (verbatim): `np.array`, `np.min`, `np.max`,
  `np.sum`, `np.bincount`, `np.nonzero`, `np.where`, `np.random.RandomState`,
  **NumPy array broadcasting**, and "floating point numbers."
- **Tools permitted:** `pdb` / `pdb++` (recommended in the email itself);
  Google "AI Overview" results allowed; **no Claude Code, Cursor, or Copilot.**

### 1.2 Indirectly supported (CodeSignal product surface)

CodeSignal *does* have a documented "Bugfix" task type and a published
"Debugging Code Using Python" course, so the existence of a debugging-only
assessment lane on the platform is well-established:

- CodeSignal's **Bugfix format** is officially described as "finding and
  correcting a *single* mistake within an otherwise correct block of
  pre-written code" with a per-line character-modification limit
  ([CodeSignal blog: Bug fixing](https://codesignal.com/blog/engineering/bug-fixing/)).
  *However*, the email's framing ("fix the root cause so the tests pass") and
  the breadth of the topic list suggest the Anthropic assessment is **not**
  the canonical 1-line Bugfix format — it's much closer to a custom
  multi-file debug-the-codebase assessment built on CodeSignal's general
  unit-test infrastructure. CodeSignal's docs explicitly note that
  custom assessments can run pytest and report pass/fail per test
  ([CodeSignal: how unit tests work in assessments](https://codesignal.com/blog/engineering/how-codesignal-makes-it-easy-to-write-and-run-unit-tests/)).
- CodeSignal also notes that **Cosmo** (their built-in AI) can be enabled or
  disabled per-assessment, and that **external AI tools are not permitted**
  in proctored assessments
  ([CodeSignal AI policy](https://support.codesignal.com/hc/en-us/articles/16957386089879-Evaluate-test-takers-AI-skills-with-Cosmo)) —
  consistent with Anthropic's "no Claude Code / Cursor / Copilot" rule.
- CodeSignal's **"Debugging Code Using Python"** course covers Python error
  decoding, logical-error tracing, exception handling, and inserting
  strategic prints / pdb stops — but its 6 units are scoped to *generic*
  Python bugs and contain no NumPy material
  ([CodeSignal course page](https://codesignal.com/learn/courses/debugging-code-using-python)).
  So the NumPy half of your assessment is **not** drawn from CodeSignal's
  standard course library — it is presumably an Anthropic-customised problem
  set.

### 1.3 Inferred (Anthropic context)

Public candidate writeups consistently describe Anthropic's culture as
"research-code feel" — numerical, NumPy-heavy, with debugging as a core
expectation. Examples:

- Sundeep Teki's research-engineer guide says common interview tasks include
  "debugging broken model training code" and "implementing core algorithms
  from classic papers"
  ([sundeepteki.org](https://www.sundeepteki.org/advice/the-ultimate-ai-research-engineer-interview-guide-cracking-openai-anthropic-google-deepmind-top-ai-labs)).
- interviewing.io says Anthropic technical rounds expect candidates to
  "handle data manipulation, model evaluation, or numerical edge-case
  debugging in Python"
  ([interviewing.io](https://interviewing.io/anthropic-interview-questions)).
- Anthropic's own [original performance take-home repo](https://github.com/anthropics/original_performance_takehome)
  explicitly describes itself as starting with "a bug that candidates needed
  to debug first" before optimization — establishing precedent that
  Anthropic builds assessments around **debug-then-extend**.

That `np.bincount`, `np.nonzero`, `np.where`, and `RandomState` are all on
the required list (rather than e.g. `einsum`, FFTs, or linear algebra) is
strong circumstantial evidence the bugs live inside something like a small
**evaluation harness**, **token/label counter**, **simple sampler**, or
**bandit/RL toy** — code shapes that are bread-and-butter at Anthropic and
Constellation Berkeley research workspaces.

---

## 2. Common bug archetypes to drill

These are the bug families I'd expect, ranked by how strongly they map onto
the email's required-knowledge list.

### 2.1 NumPy-specific (highest signal — these are nearly all on the list)

1. **`np.bincount` missing `minlength`.** `np.bincount(x)` returns an array
   of length `x.max() + 1`. If the test computes a histogram over a known
   vocabulary of size `V` but nothing in `x` happens to hit the highest id,
   the returned array is shorter than `V` and downstream broadcasting / index
   assignment silently fails or `IndexError`s. Fix: `np.bincount(x, minlength=V)`.
   Documented gotcha in the [NumPy bincount docs](https://numpy.org/doc/stable/reference/generated/numpy.bincount.html)
   and [TheLinuxCode bincount writeup](https://thelinuxcode.com/numpybincount-in-python-fast-frequency-counting-weighted-bins-and-real-world-patterns/).
2. **`np.bincount` weights dtype.** With `weights=`, `bincount` returns
   floats; without, ints. Tests asserting `result.dtype == np.int64` will
   silently fail when weights are present.
3. **`np.where` confusion: 1-arg vs 3-arg.** `np.where(cond)` returns a
   tuple of index arrays (like `np.nonzero`); `np.where(cond, a, b)`
   returns elementwise selection. A common bug is unpacking
   `idxs = np.where(mask)` and indexing with the *tuple* instead of
   `idxs[0]`, or vice versa.
4. **`np.nonzero` returns a tuple.** `np.nonzero(arr)` always returns a
   tuple of length `arr.ndim`. Forgetting to index `[0]` for a 1-D array
   produces shape-`(1, n)`-looking objects.
5. **Broadcasting shape `(n,)` vs `(n, 1)`.** Subtracting `a` from `b`
   when `a.shape == (n,)` and `b.shape == (n, 1)` does **not** raise — it
   broadcasts to `(n, n)`. Classic silent bug. Reference:
   [NumPy broadcasting docs](https://numpy.org/doc/stable/user/basics.broadcasting.html),
   [SparkCodeHub: debugging broadcasting errors](https://www.sparkcodehub.com/numpy/advanced/debugging-broadcasting-errors).
6. **`RandomState` shared-state surprise.** Calling `np.random.seed(...)`
   anywhere mutates the global RandomState, breaking reproducibility for
   any other code that reads from `np.random.*`. The fix is to instantiate
   `rng = np.random.RandomState(seed)` and pass it explicitly. References:
   [scientific-python blog](https://blog.scientific-python.org/numpy/numpy-rng/),
   [numpy/numpy#15322](https://github.com/numpy/numpy/issues/15322),
   [shap/shap#4403](https://github.com/shap/shap/issues/4403).
7. **`RandomState` consumed twice / out of order.** A test that asserts a
   specific sample expects exact draws in a specific order; calling an
   extra `.rand()` somewhere shifts every downstream sample by one.
8. **Floating-point equality.** Tests using
   `assertAlmostEqual` / `np.allclose` succeed even when the candidate's
   formula is slightly wrong; tests using `assertEqual` on floats fail
   spuriously. Watch for `1/3 != 0.333333…`, accumulated rounding in
   `np.sum`, and order-of-summation differences vs `math.fsum`.
9. **`np.sum` axis bugs.** `np.sum(a)` (no axis) collapses to scalar;
   `np.sum(a, axis=0)` collapses rows. A test expecting a per-column total
   and a candidate calling `np.sum(a, axis=1)` is the canonical off-by-one-
   axis bug.
10. **`np.min` / `np.max` on empty arrays** raises `ValueError`. A defensive
    `min(default=...)` or guard may be the fix the test expects.
11. **`np.array` dtype coercion.** Mixing ints and floats yields a float
    array; mixing ints and Python `None` raises. Mixing in a string
    silently makes the whole array dtype object/string.

### 2.2 Pure Python (also on the list)

12. **Mutable default argument** (`def f(x, memo={})` bug) —
    [Hitchhiker's Guide gotchas](https://docs.python-guide.org/writing/gotchas/),
    [Python Morsels](https://www.pythonmorsels.com/mutable-default-arguments/).
13. **Recursion missing / wrong base case** — the dominant cause of
    `RecursionError` and the most-asked Python bug archetype in interviews
    ([Codecademy recursion cheatsheet](https://www.codecademy.com/learn/algorithmic-concepts-python/modules/recursion-python-interview-prep/cheatsheet)).
14. **Recursive function not propagating the return value** — common when
    converting iterative to recursive ([py4u writeup](https://www.py4u.org/blog/python-recursion-with-list-returns-none/)).
15. **List-comprehension scope leak.** In Python 3, the comprehension
    variable does *not* leak — but `lambda`/closure captures inside a
    comprehension *do* late-bind to the loop variable. Classic bug:
    `[lambda: i for i in range(3)]` — every lambda returns 2.
16. **`typing.NamedTuple` field-order bug.** Fields with defaults must come
    after fields without defaults (`TypeError` at class-definition time).
    Subclassing a NamedTuple to add fields silently doesn't add them to the
    tuple layout ([typing spec](https://typing.python.org/en/latest/spec/namedtuples.html),
    [death.andgravity NamedTuples writeup](https://death.andgravity.com/namedtuples)).
    If a test does `Point(x=1, y=2)` and the candidate's fields are
    declared `(y: int, x: int)`, all positional construction silently
    swaps coordinates.
17. **`unittest` discovery quirks.** `setUp` runs before *every* test;
    state leaked into a class attribute persists across tests. A bug
    where the candidate fix passes one test in isolation but fails when
    the suite runs in order is almost always shared mutable state.
18. **Class vs instance attribute mutation.** A `class Counter: log = []`
    shared across all instances is a famous bug shape, related to mutable
    defaults.
19. **Off-by-one in slicing.** `a[i:j]` is half-open. Loops written as
    `for i in range(len(a))` paired with `a[i:i+window]` at boundary `i =
    len(a) - window + 1` tend to silently truncate.
20. **Integer division `//` vs float division `/`.** Common in stats /
    averaging code where a Python 2 mental model leaks in.

---

## 3. Mock interview questions (only those I can ground in real sources)

Each mock cites the source(s) that justify proposing it. I'm deliberately
**not** inventing problem statements that imply I know what the actual
Anthropic test contains — I don't.

### Mock 1 — "label histogram off-by-one"

A `class LabelStats(NamedTuple)` stores `(num_classes: int,
counts: np.ndarray)`. A method `from_labels(labels: np.ndarray)` calls
`np.bincount(labels)` and stores it. The test fixture has
`num_classes = 10` but the test labels happen to never include class `9`.
The test `assertEqual(stats.counts.shape, (10,))` fails. Fix: pass
`minlength=num_classes`.
**Sources:** required topics include `np.bincount`, `NamedTuple`, `np.array`;
the `minlength` gotcha is explicitly documented in
[NumPy bincount docs](https://numpy.org/doc/stable/reference/generated/numpy.bincount.html)
and [TheLinuxCode bincount guide](https://thelinuxcode.com/numpybincount-in-python-fast-frequency-counting-weighted-bins-and-real-world-patterns/).

### Mock 2 — "broadcast a (n,) against (n, 1)"

A function `pairwise_diffs(x: np.ndarray) -> np.ndarray` is supposed to
return an `(n, n)` matrix where `out[i, j] = x[i] - x[j]`. The buggy
implementation does `x - x` (shape `(n,)`), which returns zeros. The fix
is `x[:, None] - x[None, :]`.
**Sources:** required topics include `np.array`, broadcasting; gotcha is
canonical and documented at the [NumPy broadcasting page](https://numpy.org/doc/stable/user/basics.broadcasting.html)
and [SparkCodeHub broadcasting debug guide](https://www.sparkcodehub.com/numpy/advanced/debugging-broadcasting-errors).

### Mock 3 — "RandomState reproducibility leak"

A class `Sampler` constructs `self.rng = np.random.RandomState(seed)` in
`__init__` but a helper method calls `np.random.choice(...)` (the global
RNG, not `self.rng.choice(...)`). A test seeds an outer `Sampler(seed=0)`,
runs another piece of code that calls `np.random.seed(42)`, then runs the
sampler — the test expects the same output regardless. It currently fails
because the global RNG was mutated.
**Sources:** required topics include `np.random.RandomState`; gotcha is
documented at [scientific-python.org RNG best practices](https://blog.scientific-python.org/numpy/numpy-rng/),
[numpy/numpy#15322](https://github.com/numpy/numpy/issues/15322).

### Mock 4 — "where 1-arg vs 3-arg confusion"

A function `first_positive_index(x: np.ndarray) -> int` does
`return np.where(x > 0)[0]` but a unit test asserts the return is an
`int`, not an array. Fix: `return int(np.where(x > 0)[0][0])`. A
companion function `clip_negative(x)` is supposed to use the 3-arg form
(`np.where(x < 0, 0, x)`) but instead uses `x[np.where(x < 0)] = 0`,
mutating the input — the test asserts the input is unchanged.
**Sources:** required topics include `np.where`, `np.nonzero`; the 1-arg/
3-arg ambiguity is documented in the NumPy docs; the
"don't mutate input" expectation is the kind of constraint that the
email's "use the test suite as the final word" rule directly applies to.

### Mock 5 — "recursion base case missing / mutable default"

A recursive `flatten(lst, acc=[])` accumulator-style function is provided
with a unit test that calls `flatten([1, [2, 3]])` twice in two separate
tests. The second test fails because `acc` is the same list object and
contains the previous test's results. Fix: `acc=None` then
`if acc is None: acc = []`.
**Sources:** required topics include recursion; mutable-default gotcha is
documented in [Hitchhiker's Guide gotchas](https://docs.python-guide.org/writing/gotchas/)
and [Python Morsels](https://www.pythonmorsels.com/mutable-default-arguments/).

### Mock 6 — "NamedTuple positional-construction swap"

A `class Box(NamedTuple)` is declared with fields `(height, width, depth)`
but a constructor helper builds boxes positionally as
`Box(width, height, depth)`. Tests reading `.width` get the height value.
The fix is renaming or fixing the call site.
**Sources:** required topics include `NamedTuple`; field-order gotcha is
covered in the [typing spec for named tuples](https://typing.python.org/en/latest/spec/namedtuples.html)
and [death.andgravity NamedTuple article](https://death.andgravity.com/namedtuples).

### Mock 7 — "axis bug in mean computation"

A `mean_per_feature(X)` function meant to return a `(num_features,)` vector
calls `np.sum(X, axis=1) / X.shape[1]` instead of `axis=0 / X.shape[0]`.
Fix the axis. Pair with a floating-point tolerance test (`np.allclose`)
to highlight the difference between exact and approximate equality.
**Sources:** required topics include `np.sum`, broadcasting, "floating
point numbers"; axis bugs are the canonical NumPy bug
([SparkCodeHub shape mismatches](https://www.sparkcodehub.com/numpy/data-analysis/troubleshooting-shape-mismatches)).

### Mock 8 — "list-comprehension late-binding closure"

A function `make_callbacks(n)` returns `[lambda: i for i in range(n)]`.
A test asserts `callbacks[0]() == 0`. Fix: `lambda i=i: i` or use
`functools.partial`.
**Sources:** required topics include list comprehensions and classes/
methods; late-binding closure gotcha is one of the most-cited Python
gotchas in [Hitchhiker's Guide](https://docs.python-guide.org/writing/gotchas/).

> I considered an additional mock around `unittest`'s `setUp` / class-level
> state leakage but couldn't find a sufficiently canonical writeup that
> isn't just the stdlib docs, so I'm holding off — propose this as drill #9
> only if the email language hints at it.

---

## 4. What's Anthropic-flavoured vs generic

### Anthropic-flavoured signals

- **"Use the test suite as the final word."** This is unusual — most
  interview prompts ask candidates to *think about edge cases*. Anthropic
  here is explicitly telling you the **specification is the test suite**.
  This implies: (a) bugs in the candidate code that produce values the
  tests don't check are not bugs the candidate needs to fix; (b) the
  intended workflow is `pytest` / `unittest`-driven — read failure, find
  cause, fix, rerun. This matches the Anthropic engineering blog's
  description of how Claude Code itself debugs ("reads the errors, fixes
  the code, and runs the suite again until everything passes" —
  paraphrased from
  [interviewcoder Anthropic SE writeup](https://www.interviewcoder.co/blog/anthropic-software-engineer-interview)).
- **NumPy-heavy required-topic list.** Among public Anthropic interview
  signals, the only consistent NumPy theme is "research-code feel" — see
  Sundeep Teki and interviewing.io. The specific call-out of `bincount`
  and `RandomState` (vs e.g. linear algebra or einsum) suggests the test
  domain is **classification / counting / sampling code**, not deep
  learning. This fits Constellation's safety/alignment research bent
  (eval harnesses, behavioural-test counters, simple bandits) much better
  than the ML-systems / performance fellowship track.
- **`pdb` recommended, no Claude Code / Cursor / Copilot.** Anthropic
  publicly tracks AI cheating on their own assessments
  ([Built In: Anthropic cheating scandal](https://builtin.com/articles/reimagining-coding-interview),
  [Anthropic engineering: AI-resistant evaluations](https://www.anthropic.com/engineering/AI-resistant-technical-evaluations))
  and is shifting toward formats AI struggles with — debugging an
  *existing* codebase under `pdb` is exactly that kind of format, since
  reading a stack trace and stepping through state is harder for LLMs to
  do well in proctored settings without access to runtime.
- **"AI Overview" allowed.** This is the same boundary as the public
  90-min CodeSignal — basic Google searches for syntax are fine, full LLM
  codegen is not. CodeSignal's official
  [AI policy](https://support.codesignal.com/hc/en-us/articles/16957386089879-Evaluate-test-takers-AI-skills-with-Cosmo)
  matches this.

### Generic CodeSignal-flavoured signals

- The platform's Bugfix and unit-test infrastructure are
  [well-documented](https://codesignal.com/blog/engineering/how-codesignal-makes-it-easy-to-write-and-run-unit-tests/).
- The proctoring rules and "no external AI" stance are platform-wide.
- The "fix the code so the tests pass" framing is CodeSignal's standard
  Bugfix idiom, just scaled up from 1-line to a full codebase.

---

## 5. 5-day preparation plan

Given the strong signal that the bugs likely live in `class`-organized,
`NamedTuple`-using, NumPy-flavoured numeric code with a `unittest` harness,
and that pdb is permitted:

### Day 1 — NumPy gotcha drill (3 hours)

- Read the [NumPy broadcasting page](https://numpy.org/doc/stable/user/basics.broadcasting.html)
  end-to-end. Type out by hand the shape of `a[:, None] + b[None, :]` for
  `a, b` of shapes `(n,), (m,)`.
- Read `bincount`, `where`, `nonzero`, `argmin`/`argmax` docs. For each,
  write a 5-line snippet that triggers the most common bug (`minlength`
  short, `where` 1-arg vs 3-arg, `nonzero` returns tuple, axis confusion).
- Practice `RandomState`: build a tiny `Sampler` class that takes
  `seed: int`, has a `.draw()` method, and prove via assertion that
  two `Sampler(seed=0)` instances produce identical streams *even if*
  some other code calls `np.random.seed(42)` between them.

### Day 2 — Pure-Python gotcha drill (3 hours)

- Mutable default arguments, late-binding closures in comprehensions,
  list-comp scoping in Python 3, and class vs instance attribute mutation
  — write a buggy and a fixed version of each, plus a `unittest` that
  distinguishes them.
- `typing.NamedTuple`: build one with a default field, swap field order
  to break a positional constructor, then fix it. Compare with
  `collections.namedtuple` and `dataclasses.dataclass(frozen=True)` so
  you can recognize whichever the assessment uses.
- Recursion: implement `flatten`, `tree_sum`, and `merge_sort` from
  scratch with a unit test, deliberately introduce missing-base-case and
  missing-return-value bugs, then fix.

### Day 3 — Tooling: pdb and unittest fluency (2 hours)

- Practice `pdb` until these are reflexes: `b file.py:42`, `c`, `n`,
  `s`, `p var`, `pp var`, `w` (where), `u` / `d` (frame nav), `!`
  (run python expr), `interact`, `tbreak`, `ll` (longlist).
- Install `pdbpp` (`pip install pdbpp`) and verify the colored
  longlist & sticky mode work in your terminal — your email recommends
  this. **Do not rely on this if the test environment doesn't have it
  installed**; have a plan B with bare `pdb`.
- Run `python -m pdb -c continue script.py` so you drop into pdb on
  uncaught exceptions. Practice `pytest --pdb` and
  `python -m unittest -v`.

### Day 4 — Build an end-to-end mock (3 hours)

Build a small (~150 LOC) "research evaluation harness" that:

- Defines `class EvalConfig(NamedTuple)` with seed, num_classes,
  num_samples.
- Has a `class Sampler` taking a `RandomState` and producing labels.
- Has a `class Stats` that aggregates labels via `np.bincount`.
- Has a recursive `flatten_results` helper.
- Comes with a `unittest.TestCase` of ~10 tests.

Plant 4–5 of the bugs from §2. Walk away. Come back the next morning.
Set a 60-minute timer and try to fix all the bugs purely from the
failing test output.

### Day 5 — Speed run + meta-strategy (2 hours)

- Run two more 60-minute mocks (use [PaulLockett's CodeSignal practice
  framework repo](https://github.com/PaulLockett/CodeSignal_Practice_Industry_Coding_Framework)
  for general flavour, then Day 4's harness flavour). Time-box: read all
  test names first (3 min); run the suite, read all failure messages
  (5 min); prioritize the most-load-bearing bug first (5 min);
  fix-and-rerun loop (45 min); buffer (2 min).
- **Strategy rule from the email:** if a failure is in code your fix
  doesn't touch and isn't checked by any test, ignore it.
- Re-read the gotcha list in §2 the morning of the test.

---

## 6. Bibliography (every URL cited)

### Anthropic interview process (general)

- interviewing.io — Anthropic interview questions:
  https://interviewing.io/anthropic-interview-questions
- IGotAnOffer — Anthropic interview process timeline:
  https://igotanoffer.com/en/advice/anthropic-interview-process
- IGotAnOffer — common Anthropic interview questions:
  https://igotanoffer.com/en/advice/anthropic-interview-questions
- Sundeep Teki — AI research engineer interview guide (OpenAI / Anthropic /
  DeepMind):
  https://www.sundeepteki.org/advice/the-ultimate-ai-research-engineer-interview-guide-cracking-openai-anthropic-google-deepmind-top-ai-labs
- Sundeep Teki — Anthropic CodeSignal assessment guide:
  https://www.sundeepteki.org/advice/anthropic-codesignal-assessment-guide
- Exponent — Anthropic AI Safety Fellow interview guide:
  https://www.tryexponent.com/guides/anthropic-ai-safety-fellow-interview
- Final Round AI — How to ace the Anthropic CodeSignal:
  https://www.finalroundai.com/blog/how-to-ace-your-anthropic-code-signal-assessment-a-step-by-step-guide
- LinkJob — How I practiced Anthropic CodeSignal questions:
  https://www.linkjob.ai/interview-questions/codesignal-anthropic-practice/
- LinkJob — Anthropic coding interview question bank:
  https://www.linkjob.ai/interview-questions/anthropic-coding-interview/
- Interview Coder — Top 30 Anthropic SE interview questions:
  https://www.interviewcoder.co/blog/anthropic-software-engineer-interview
- Built In — "Is Anthropic's cheating scandal the end of the coding interview?":
  https://builtin.com/articles/reimagining-coding-interview
- Anthropic engineering — AI-resistant technical evaluations:
  https://www.anthropic.com/engineering/AI-resistant-technical-evaluations
- Anthropic — original performance take-home repo (debug-then-extend prior
  art): https://github.com/anthropics/original_performance_takehome

### Anthropic Fellows / Constellation

- Anthropic alignment blog — Fellows program 2026:
  https://alignment.anthropic.com/2025/anthropic-fellows-program-2026/
- Anthropic Fellows generic Greenhouse posting:
  https://job-boards.greenhouse.io/anthropic/jobs/5023394008
- Anthropic Fellows — AI Safety:
  https://job-boards.greenhouse.io/anthropic/jobs/5183044008
- Constellation Astra Fellowship overview:
  https://www.constellation.org/programs/astra-fellowship

### Candidate writeups

- Goncharov / Fail Learn Repeat — "I failed my Anthropic interview…":
  https://blog.faillearnrepeat.net/blog/i-failed-my-anthropic-interview-and-came-to-tell-you-all-about-it-so-you-dont-have-to/
- Zackhui (Medium) — "I didn't get the Anthropic Fellowship…":
  https://medium.com/@zackhui52/i-didnt-get-the-anthropic-fellowship-but-i-got-a-story-and-a-cigar-4615fea6edc0
- Hacker News thread — "Flunking my Anthropic interview again":
  https://news.ycombinator.com/item?id=45064284

### CodeSignal platform documentation

- CodeSignal — Bugfix assessment format:
  https://codesignal.com/blog/engineering/bug-fixing/
- CodeSignal — How unit tests work in assessments:
  https://codesignal.com/blog/engineering/how-codesignal-makes-it-easy-to-write-and-run-unit-tests/
- CodeSignal — "Debugging Code Using Python" course:
  https://codesignal.com/learn/courses/debugging-code-using-python
- CodeSignal — Cosmo / AI policy:
  https://support.codesignal.com/hc/en-us/articles/16957386089879-Evaluate-test-takers-AI-skills-with-Cosmo
- CodeSignal — Question library:
  https://support.codesignal.com/hc/en-us/articles/360045744053-The-CodeSignal-Question-Library
- PaulLockett — CodeSignal Industry Coding Framework practice repo:
  https://github.com/PaulLockett/CodeSignal_Practice_Industry_Coding_Framework

### NumPy gotchas

- NumPy — `bincount` docs:
  https://numpy.org/doc/stable/reference/generated/numpy.bincount.html
- NumPy — broadcasting basics:
  https://numpy.org/doc/stable/user/basics.broadcasting.html
- TheLinuxCode — `bincount` real-world patterns:
  https://thelinuxcode.com/numpybincount-in-python-fast-frequency-counting-weighted-bins-and-real-world-patterns/
- SparkCodeHub — debugging broadcasting errors:
  https://www.sparkcodehub.com/numpy/advanced/debugging-broadcasting-errors
- SparkCodeHub — troubleshooting shape mismatches:
  https://www.sparkcodehub.com/numpy/data-analysis/troubleshooting-shape-mismatches
- scientific-python.org — best practices for NumPy RNG:
  https://blog.scientific-python.org/numpy/numpy-rng/
- numpy/numpy issue 15322 — global state for `numpy.random`:
  https://github.com/numpy/numpy/issues/15322
- shap/shap issue 4403 — incorrect random-state restoration:
  https://github.com/shap/shap/issues/4403

### Python gotchas

- Python typing spec — Named Tuples:
  https://typing.python.org/en/latest/spec/namedtuples.html
- death.andgravity — NamedTuples in a post-dataclasses world:
  https://death.andgravity.com/namedtuples
- Hitchhiker's Guide to Python — common gotchas:
  https://docs.python-guide.org/writing/gotchas/
- Python Morsels — mutable default arguments:
  https://www.pythonmorsels.com/mutable-default-arguments/
- py4u — recursive Python function returning None:
  https://www.py4u.org/blog/python-recursion-with-list-returns-none/
- Codecademy — recursion in Python interview prep cheatsheet:
  https://www.codecademy.com/learn/algorithmic-concepts-python/modules/recursion-python-interview-prep/cheatsheet

---

## 7. Uncertainty / honesty section

Calibrated confidence levels on each claim in this outline:

- **§1.1 (the email's stated format and required-topic list).** Confidence:
  certain — sourced from the email itself, which is authoritative.
- **§1.2 (CodeSignal's Bugfix and debugging-course infrastructure exists).**
  Confidence: high — directly documented on CodeSignal's own blog and
  knowledge base.
- **§1.2 (Anthropic's debugging assessment is *not* the canonical 1-line
  Bugfix format).** Confidence: medium — based on the email's "fix the root
  cause so tests pass" framing, which doesn't match the 1-line constraint.
  Could be wrong if Anthropic uses a sequence of single-line bugfix tasks.
- **§1.3 (Anthropic culture is research-code, NumPy-heavy, debug-as-core).**
  Confidence: high — multiple independent public sources
  (interviewing.io, sundeepteki.org, the open-sourced performance take-home).
- **§1.3 (the bug domain is likely an "evaluation harness / counter /
  sampler" shape).** Confidence: medium-low — this is *inference* from the
  topic list. Could equally be a small RL gridworld, a token-frequency
  counter, or a stats helper for an experiment runner. I am specifically
  not claiming any candidate has reported any of these.
- **§2 (the bug archetypes).** Confidence: high *that these are the canonical
  bug archetypes* in their respective topic areas; medium *that they are
  the specific bugs Anthropic chose*. The bug-archetype list is grounded in
  documentation and well-known gotcha guides.
- **§3 (mock interview questions).** Confidence: each mock combines a real
  required-knowledge topic with a real, documented gotcha, but **none of
  these mocks comes from a candidate who actually took the assessment**.
  The user should treat them as plausible drills, not previews of real
  questions. I could not propose more mocks honestly because there are no
  more grounded combinations I'm willing to claim.
- **§4 (Anthropic-flavoured vs generic).** Confidence: medium-high —
  the "use the test suite as the final word" rule is verbatim from the
  email, and the AI-resistant-evaluation framing is sourced to Anthropic's
  own engineering blog.
- **§5 (5-day prep plan).** Confidence: high *as preparation strategy* —
  drills are aligned with the email's required-topic list and standard
  CodeSignal mechanics.

**What is missing from this research that I'd want before the test:**

1. A candidate writeup that explicitly mentions a 60-min Python debugging
   CodeSignal sent by Constellation. I could not find one. It's possible
   this assessment is recent, lightly used, or candidates are under NDA.
2. Any verbatim problem statement. None exists publicly.
3. Specific bug instances ("the bug was in a numpy bincount with a missing
   length parameter" or "broadcasting gotcha with shape (n,) vs (n,1)") in
   actual writeups — none found. Every such phrase in this outline is my
   own inference from documented gotchas, not a candidate quote.

If anything in §3 turns out to match the real test exactly, that's lucky
inference, not insider knowledge. Prepare across the *whole* gotcha space,
not just the mocks.
