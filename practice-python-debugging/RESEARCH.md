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

---

## 8. Harder + LLM-specific bug archetypes (research pass 2)

> **Scope of this pass.** §2 covered the *canonical* NumPy/Python gotchas.
> This section goes one layer deeper: (a) **subtler** bug shapes that survive
> a casual read, and (b) bugs that specifically live in **LLM / ML research
> code** — softmax, attention, tokenizers, samplers, batched loss. The
> reasoning for why this matters: the email's required-knowledge list
> (`bincount`, `RandomState`, `np.where`, broadcasting, floating point) plus
> Anthropic's well-documented "research-code feel" makes a small
> softmax/sampler/eval-harness the single most likely codebase shape. None of
> this is a leak — it's inference from the topic list cross-checked against
> the numerical-stability and ML-engineering literature. Confidence notes are
> at the end of the section.

### 8.1 Catalogue of harder / LLM-specific bug archetypes

Each entry: one-line description · why it's subtle · how it surfaces in a
failing test · citation.

**Numerical stability**

1. **Naive softmax — no max subtraction.** `np.exp(logits)` without
   `logits - logits.max()`. *Subtle:* passes every test with small logits;
   only blows up on large-magnitude inputs. *Surfaces as:* a test with big
   logits asserts probabilities sum to 1 / match expected, gets `nan`
   (`inf/inf`). Fix: `e = np.exp(x - np.max(x, axis=-1, keepdims=True))`.
   ([Jay Mody — stable softmax](https://jaykmody.com/blog/stable-softmax/),
   [Brian Lester — numerically stable softmax](https://blester125.com/blog/softmax.html))
2. **Cross-entropy / NLL via `log(softmax(...))` instead of log-sum-exp.**
   When a softmax probability underflows to `0.0`, `np.log(0.0) = -inf`.
   *Subtle:* the softmax itself looks fine; the loss is what breaks. *Surfaces
   as:* a loss test returns `inf`/`nan` for a confident prediction. Fix:
   `logp = x - max(x) - log(sum(exp(x - max(x))))`.
   ([Jay Mody — stable softmax](https://jaykmody.com/blog/stable-softmax/),
   [Accurately computing log-sum-exp and softmax, IMA J. Num. Anal.](https://academic.oup.com/imajna/article/41/4/2311/5893596))
3. **Log-probability accumulation by multiplying probs instead of summing
   log-probs.** A sequence scorer does `prob *= p[token]` over a long
   sequence; the product underflows to `0.0`. *Subtle:* short sequences pass.
   *Surfaces as:* a long-sequence test expects a finite negative log-prob,
   gets `0.0` or `-inf`. Fix: accumulate `logprob += np.log(p[token])`.
   ([John D. Cook — soft maximum](https://www.johndcook.com/blog/2010/01/20/how-to-compute-the-soft-maximum/))
4. **Catastrophic cancellation in a variance/std formula.**
   `mean(x**2) - mean(x)**2` loses precision when the two terms are large and
   close. *Subtle:* `assertAlmostEqual` may still pass at low decimals; a
   tight tolerance test fails. Fix: subtract the mean first
   (`mean((x - mean(x))**2)`).
   ([Accurately computing log-sum-exp and softmax](https://academic.oup.com/imajna/article/41/4/2311/5893596))

**Attention**

5. **Softmax over the wrong axis in attention.** `softmax(scores)` with no
   axis (or `axis=0`) instead of `axis=-1`. *Subtle:* output still has the
   right shape and still "looks normalized." *Surfaces as:* attention rows
   don't sum to 1, or the output matches a transpose of the expected. Fix:
   `axis=-1`, `keepdims=True`.
   ([Eli Bendersky — notes on implementing attention](https://eli.thegreenplace.net/2025/notes-on-implementing-attention/),
   [Jay Mody — GPT in 60 lines of NumPy](https://jaykmody.com/blog/gpt-from-scratch/))
6. **Mask shape `(batch, seq)` vs `(batch, seq, seq)`.** A padding mask is
   `(B, S)` but the scores are `(B, S, S)`; adding them broadcasts to the
   wrong axis (masks *keys* uniformly instead of per query-row, or raises).
   *Subtle:* with `B == S` it may not even raise. *Surfaces as:* a test with
   `B != S` raises a broadcast error, or masked positions leak attention.
   Fix: reshape mask to `(B, 1, S)` (broadcast over query rows) or build a
   full `(B, S, S)` mask. ([MachineLearningMastery — attention masking](https://machinelearningmastery.com/a-gentle-introduction-to-attention-masking-in-transformer-models/),
   [pytorch/pytorch#99282](https://github.com/pytorch/pytorch/issues/99282))
7. **Missing / wrong `1/sqrt(d)` scaling.** Forgetting the scale, or scaling
   by `sqrt(seq_len)` / `k.shape[1]` instead of the head dim `k.shape[-1]`.
   *Subtle:* output shape is correct; only the values are off. *Surfaces as:*
   numeric mismatch vs a reference attention output. Fix:
   `scores / np.sqrt(k.shape[-1])`.
   ([Eli Bendersky — implementing attention](https://eli.thegreenplace.net/2025/notes-on-implementing-attention/))
8. **Causal mask applied with `0` instead of `-inf`, or off-by-one
   diagonal.** Using `np.where(mask == 0, 0.0, scores)` (zeroes the score,
   which still gets positive softmax weight) instead of `-np.inf`; or
   `np.triu(m, k=0)` vs `k=1` so the token can't attend to itself / can
   attend one step into the future. *Subtle:* a single shifted token. *Surfaces
   as:* a causal-attention test where position `t` sees `t+1`. Fix: mask with
   `-np.inf` *before* softmax; check `np.tril`/`triu` offset.
   ([Eli Bendersky — implementing attention](https://eli.thegreenplace.net/2025/notes-on-implementing-attention/),
   [Abhik Sarkar — masked & causal attention](https://www.abhik.ai/concepts/attention/masked-attention))
9. **Softmax denominator summed over the wrong axis** (the query axis instead
   of the key axis), so each column normalizes instead of each row. Fix:
   denominator `axis=-1, keepdims=True`.
   ([Jay Mody — GPT in 60 lines of NumPy](https://jaykmody.com/blog/gpt-from-scratch/),
   [onnx/onnx#5655 — softmax axis bug](https://github.com/onnx/onnx/issues/5655))

**Tokenizer / BPE**

10. **Vocabulary off-by-one / special-token id collision.** `eos_id` set to
    `len(vocab)` (out of range) or reusing id `0` for both `pad` and a real
    token. *Subtle:* most text never hits the colliding id. *Surfaces as:* an
    `IndexError` on embedding lookup, or a decode test where `pad` prints as a
    real token. ([HF — BPE tokenization](https://huggingface.co/learn/llm-course/en/chapter6/5),
    [Sebastian Raschka — BPE from scratch](https://sebastianraschka.com/blog/2025/bpe-from-scratch.html))
11. **Merge rules applied in the wrong order.** BPE merges must be applied in
    training-frequency order (rank), not vocab-id order or dict-iteration
    order. *Subtle:* many inputs tokenize identically under both orders.
    *Surfaces as:* an `encode` test produces a different (but plausible) token
    sequence. ([MartinLwx — BPE tokenizer](https://martinlwx.github.io/en/the-bpe-tokenizer/),
    [HF — BPE tokenization](https://huggingface.co/learn/llm-course/en/chapter6/5))
12. **encode/decode round-trip not lossless.** `decode(encode(s)) != s` —
    usually a join-without-separator bug, a dropped byte-level prefix space,
    or `bincount`-based frequency code that miscounts. *Surfaces as:* an
    explicit round-trip `assertEqual`. ([HF — BPE tokenization](https://huggingface.co/learn/llm-course/en/chapter6/5),
    [Tiny🔥Torch — tokenization module](https://mlsysbook.ai/tinytorch/modules/10_tokenization_ABOUT.html))
13. **`np.bincount` for token frequency missing `minlength=vocab_size`** (also
    in §2.1#1, repeated here because it's the *most* likely tokenizer-flavored
    instance): a frequency table comes back shorter than the vocab when the
    last token id is absent. ([NumPy bincount docs](https://numpy.org/doc/stable/reference/generated/numpy.bincount.html))
14. **Unbounded recursion in merge application / trie traversal.** A recursive
    BPE merge or trie walk with a base case that only triggers on exact empty
    input recurses forever on a single leftover token. *Surfaces as:*
    `RecursionError` on certain inputs.
    ([mathspp — watch out for recursion](https://mathspp.com/blog/pydonts/watch-out-for-recursion))

**Sampling / decoding**

15. **Temperature applied to probabilities instead of logits.** `probs / T`
    after softmax (or `probs ** (1/T)` without renormalizing) instead of
    `logits / T` before softmax. *Subtle:* `T = 1` hides it entirely.
    *Surfaces as:* a `T != 1` test where the distribution is wrong / doesn't
    sum to 1. ([Let's Data Science — LLM sampling params](https://letsdatascience.com/blog/llm-sampling-temperature-top-k-top-p-and-min-p-explained),
    [MachineLearningMastery — logits, softmax, sampling](https://machinelearningmastery.com/how-llms-choose-their-words-a-practical-walk-through-of-logits-softmax-and-sampling/))
16. **Top-p cutoff `<` vs `<=`, or cutting *before* vs *after* crossing p.**
    Nucleus sampling must keep the *smallest* set whose cumulative prob
    *exceeds* p — i.e. keep the token that crosses the threshold. A `<`
    comparison or shifting the cumsum by one drops that token. *Subtle:*
    only matters at the boundary token. *Surfaces as:* a top-p test expects N
    tokens kept, gets N-1. ([Top-p sampling — Wikipedia](https://en.wikipedia.org/wiki/Top-p_sampling),
    [labml.ai — nucleus sampling](https://nn.labml.ai/sampling/nucleus.html))
17. **Top-k off-by-one / wrong `argsort` direction.** `argsort` is ascending;
    taking `[:k]` gives the *k smallest* logits. Or `[-k:]` vs `[-k-1:]`.
    *Surfaces as:* a top-k test where the kept set is wrong or inverted.
    ([Aman's AI Journal — token sampling](https://aman.ai/primers/ai/token-sampling/))
18. **No renormalization after top-k/top-p filtering.** Zeroing out filtered
    probabilities but not dividing by the new sum, so `np.random.choice(p=...)`
    raises "probabilities do not sum to 1" — or silently biases. *Surfaces as:*
    a `ValueError` from `choice`, or a distribution test failing.
    ([labml.ai — nucleus sampling](https://nn.labml.ai/sampling/nucleus.html))
19. **`RandomState` draw-order / wrong-RNG bug in the sampler.** An extra
    `rng.random()` (e.g. a debug line, or filtering done with the same rng)
    shifts every subsequent draw; or the sampler uses global `np.random.*`
    instead of the injected `RandomState`. *Subtle:* output is still "valid,"
    just not the seeded-reproducible value the test pins. *Surfaces as:* a
    seeded test asserting an exact token id fails.
    ([scientific-python — NumPy RNG best practices](https://blog.scientific-python.org/numpy/numpy-rng/),
    [numpy/numpy#15322](https://github.com/numpy/numpy/issues/15322))
20. **Greedy `argmax` tie-breaking.** `np.argmax` returns the *first* max
    index; if the reference (or a test fixture) expects last-index or random
    tie-breaking, a tie produces a different token. *Surfaces as:* a greedy-
    decode test failing only on inputs with tied logits.
    ([MachineLearningMastery — logits, softmax, sampling](https://machinelearningmastery.com/how-llms-choose-their-words-a-practical-walk-through-of-logits-softmax-and-sampling/))

**Broadcasting / batched loss + harder pure-Python**

21. **`keepdims=False` in a normalization step.** `x / x.sum(axis=-1)` where
    the sum collapses to `(B,)` and then broadcasts against `(B, V)` from the
    *right* — i.e. it tries to align `V` with `B`. *Subtle:* if `B == V` it
    silently produces garbage instead of raising. Fix: `keepdims=True`.
    ([Eli Bendersky — implementing attention](https://eli.thegreenplace.net/2025/notes-on-implementing-attention/),
    [DeepLearning.AI forum — keepdims in np.sum](https://community.deeplearning.ai/t/dba-np-sum-dtanh-axis-1-or-keepdims-true/297708))
22. **`(n,)` vs `(n,1)` silent broadcast in batched code.** Subtracting a
    `(batch,)` vector from a `(batch, dim)` matrix broadcasts the wrong way
    (or to `(batch, batch)` if the vector is `(batch,)` and the matrix is
    `(dim, batch)`). NumPy does *not* raise. *Surfaces as:* a loss/metric off
    by a transpose or with the wrong shape. Fix: `v[:, None]`.
    ([Medium — (n,) vs (n,1) in ML](https://medium.com/@prathik.codes/numpy-array-shapes-n-vs-n-1-in-machine-learning-50cca6f93502),
    [SparkCodeHub — debugging broadcasting errors](https://www.sparkcodehub.com/numpy/advanced/debugging-broadcasting-errors))
23. **Per-batch loss averaged over the wrong axis** (`np.mean(losses, axis=0)`
    vs `axis=1`, or a stray `np.mean` that collapses the batch you meant to
    keep). *Surfaces as:* a loss test getting a scalar where it expects a
    `(batch,)` vector, or a number that's `mean`-of-`mean` ≠ true mean when
    rows have unequal valid lengths (masked tokens).
    ([SparkCodeHub — troubleshooting shape mismatches](https://www.sparkcodehub.com/numpy/data-analysis/troubleshooting-shape-mismatches))
24. **Mutated shared accumulator across recursive branches.** A recursive
    tree/merge walk passes one `list` (or `np.ndarray`) accumulator down both
    branches; the left branch's appends are visible to the right branch
    because it's the *same object*. *Subtle:* differs from the classic mutable-
    default bug — the default is fine, the *aliasing within one call tree* is
    the bug. *Surfaces as:* a recursion test where results bleed between
    subtrees. Fix: pass a copy at the branch point, or return-and-merge
    instead of mutating. ([copyprogramming — list mutation in recursion](https://copyprogramming.com/howto/python-lists-mutation-recursion-issue),
    [mathspp — watch out for recursion](https://mathspp.com/blog/pydonts/watch-out-for-recursion))
25. **Recursion base-case ordering / wrong base case.** Checking the recursive
    case before the base case, or a base case on `len == 0` when the divide-
    and-conquer split can hand a child `len == 1`. *Surfaces as:* `IndexError`
    or `RecursionError` on small inputs only.
    ([mathspp — watch out for recursion](https://mathspp.com/blog/pydonts/watch-out-for-recursion))
26. **`NamedTuple` default / `_replace` / inheritance pitfalls.** A
    `typing.NamedTuple` subclass that "adds" a field (silently ignored — the
    tuple layout doesn't change); or `_replace` with a misspelled field
    (raises `ValueError` at call time, not definition time); or a mutable
    default (`counts: list = []`) shared across all instances. *Surfaces as:*
    a test reading the "new" field gets the parent's value, or instances
    share state. ([typing spec — Named Tuples](https://typing.python.org/en/latest/spec/namedtuples.html),
    [death.andgravity — NamedTuples](https://death.andgravity.com/namedtuples))
27. **Generator exhausted on second use.** A function returns a generator;
    a test (or the code) iterates it twice — the second pass is empty. Common
    when a "dataset" or "token stream" helper is a generator but the test
    does `len(list(...))` then re-iterates. *Surfaces as:* second assertion
    on the same object sees nothing.
    ([Hitchhiker's Guide — gotchas](https://docs.python-guide.org/writing/gotchas/))
28. **Integer vs float division in metric code.** `correct // total` (Python 3
    floor division) in an accuracy/perplexity calc, or `np.array([...],
    dtype=int)` arithmetic truncating a rate to `0`. *Surfaces as:* a metric
    test expecting `0.83` gets `0`. ([Hitchhiker's Guide — gotchas](https://docs.python-guide.org/writing/gotchas/))

### 8.2 What realistic buggy code looks like, per LLM domain

**Tokenizer / BPE.** Expect a `class BPETokenizer` with `merges` (an ordered
list/dict of pair → rank), an `encode` that repeatedly finds the
highest-priority adjacent pair and merges it, and a `decode` that joins
token strings. The realistic bug is in *priority*: iterating `self.merges`
in dict-insertion order instead of by rank, or using `min()` over pair ranks
with a `KeyError` fallback that's wrong. A second realistic bug is
`np.bincount(token_ids)` for a frequency table without `minlength=vocab_size`,
so the table is too short whenever the highest id is unused. A third:
`decode` joining with `" "` (or `""`) when the tokenizer uses a byte-level
space marker, breaking the round-trip test.

**Attention.** Expect a `scaled_dot_product_attention(q, k, v, mask=None)`
function, ~15 lines, fully NumPy. The realistic bugs cluster in four spots:
(1) `softmax` called without `axis=-1`/`keepdims=True`; (2) scaling by the
wrong dimension (`k.shape[0]` or `k.shape[1]` instead of `k.shape[-1]`, or
omitted); (3) the mask added/applied with the wrong shape — a `(B, S)`
padding mask broadcast against `(B, S, S)` scores; (4) the causal mask using
`0.0` instead of `-np.inf`, or `np.triu` with the wrong `k=` offset so the
diagonal is masked or the future leaks by one. All four keep the output
*shape* correct, which is why they survive a quick read and only a value
assertion catches them.

**Sampling / decoding.** Expect a `class Sampler` taking a
`np.random.RandomState` (or seed) plus `temperature`, `top_k`, `top_p`, and a
`sample(logits)` method. Realistic bugs: temperature applied after softmax
instead of to logits; `argsort` ascending so top-k keeps the *smallest*
logits; the top-p cumsum cutoff using `<` instead of `<=` (drops the
threshold-crossing token) or filtering then forgetting to renormalize so
`rng.choice` raises "probabilities do not sum to 1"; and an extra RNG draw
(or use of the global `np.random`) that desyncs a seeded test's expected
token id.

**Broadcasting / batched loss.** Expect a `cross_entropy(logits, targets)` or
`sequence_logprob` over a `(batch, seq, vocab)` tensor. Realistic bugs:
`logits.sum(axis=-1)` without `keepdims=True` so the normalizer broadcasts
the wrong way; averaging the loss over `axis=0` vs `axis=1`; a `(batch,)`
length vector subtracted/divided against a `(batch, seq)` matrix without a
`[:, None]`; and `mean`-of-per-row-`mean` giving the wrong number when rows
have different numbers of valid (non-pad) tokens — the fix is a masked sum
divided by the mask's token count.

### 8.3 Confidence / uncertainty note

- **Well-documented gotchas (high confidence these are real, canonical
  bugs):** stable-softmax max-subtraction (#1), log-sum-exp for CE/NLL (#2),
  softmax axis (#5, #9), `1/sqrt(d)` scaling (#7), causal mask with `-inf`
  and `triu`/`tril` offset (#8), `np.bincount` `minlength` (#13), BPE merge
  *order* mattering (#11), round-trip losslessness as a property (#12),
  temperature-on-logits (#15), top-p "smallest set exceeding p" definition
  (#16), renormalization after filtering (#18), `RandomState` global-vs-local
  (#19), `argmax` first-index tie-break (#20), `keepdims` in normalization
  (#21), `(n,)` vs `(n,1)` silent broadcast (#22), `NamedTuple`
  inheritance/`_replace` (#26), generator exhaustion (#27). Each has a
  primary source above.
- **Inference / synthesis (medium confidence — the *gotcha* is real but I am
  combining it into an "Anthropic-likely" bug shape, not quoting a candidate):**
  the specific framing of #3 (logprob accumulation), #4 (cancellation in a
  variance formula), #6 (the exact `(B,S)` vs `(B,S,S)` mask instance), #10
  (special-token id collision), #14 (recursion in merge application), #17
  (top-k `argsort` direction), #23 (loss averaged over wrong axis with
  masking), #24 (shared accumulator *within one recursive call tree*, as
  distinct from the mutable-default bug), #25 (base-case ordering), #28
  (int/float division in metrics). These are all documented *phenomena*; the
  claim that Anthropic's test uses *this* instance is my inference.
- **What I could not find:** still — as in pass 1 — **zero** public attestation
  of the specific 60-minute Constellation Python debugging assessment. Fresh
  searches (Reddit, Blind, Glassdoor, prachub, linkjob, 2026-dated guides)
  surface only the 90-minute progressive-build general CodeSignal and the AI
  Safety Fellow live round. No candidate has publicly described a
  debug-the-LLM-codebase task. Treat §8 as a *grounded study guide for the
  bug space*, not a preview.

### 8.4 Bibliography (URLs cited in this pass)

**Numerical stability / softmax / log-sum-exp**

- Jay Mody — Numerically Stable Softmax and Cross Entropy:
  https://jaykmody.com/blog/stable-softmax/
- Jay Mody — GPT in 60 Lines of NumPy:
  https://jaykmody.com/blog/gpt-from-scratch/
- Brian Lester — Numerically Stable Softmax:
  https://blester125.com/blog/softmax.html
- John D. Cook — How to compute the soft maximum:
  https://www.johndcook.com/blog/2010/01/20/how-to-compute-the-soft-maximum/
- Blanchard, Higham & Higham — Accurately computing the log-sum-exp and
  softmax functions (IMA Journal of Numerical Analysis):
  https://academic.oup.com/imajna/article/41/4/2311/5893596

**Attention**

- Eli Bendersky — Notes on implementing attention:
  https://eli.thegreenplace.net/2025/notes-on-implementing-attention/
- MachineLearningMastery — A Gentle Introduction to Attention Masking in
  Transformer Models:
  https://machinelearningmastery.com/a-gentle-introduction-to-attention-masking-in-transformer-models/
- Abhik Sarkar — Masked and Causal Attention:
  https://www.abhik.ai/concepts/attention/masked-attention
- pytorch/pytorch#99282 — MultiheadAttention is_causal ignored with
  need_weights: https://github.com/pytorch/pytorch/issues/99282
- onnx/onnx#5655 — Bug of Softmax op with different axis:
  https://github.com/onnx/onnx/issues/5655

**Tokenizer / BPE**

- Hugging Face — Byte-Pair Encoding tokenization:
  https://huggingface.co/learn/llm-course/en/chapter6/5
- Sebastian Raschka — Implementing a BPE Tokenizer From Scratch:
  https://sebastianraschka.com/blog/2025/bpe-from-scratch.html
- MartinLwx — BPE Tokenization Demystified:
  https://martinlwx.github.io/en/the-bpe-tokenizer/
- Tiny🔥Torch — Module 10: Tokenization:
  https://mlsysbook.ai/tinytorch/modules/10_tokenization_ABOUT.html

**Sampling / decoding**

- Top-p sampling — Wikipedia: https://en.wikipedia.org/wiki/Top-p_sampling
- labml.ai — Nucleus Sampling: https://nn.labml.ai/sampling/nucleus.html
- Aman's AI Journal — Token Sampling Methods:
  https://aman.ai/primers/ai/token-sampling/
- Let's Data Science — LLM Sampling Parameters Explained:
  https://letsdatascience.com/blog/llm-sampling-temperature-top-k-top-p-and-min-p-explained
- MachineLearningMastery — How LLMs Choose Their Words (logits, softmax,
  sampling):
  https://machinelearningmastery.com/how-llms-choose-their-words-a-practical-walk-through-of-logits-softmax-and-sampling/

**Broadcasting / batched loss / pure-Python**

- Medium (Prathik C) — NumPy Array Shapes: (n,) vs (n,1) in Machine Learning:
  https://medium.com/@prathik.codes/numpy-array-shapes-n-vs-n-1-in-machine-learning-50cca6f93502
- SparkCodeHub — Debugging Broadcasting Errors in NumPy:
  https://www.sparkcodehub.com/numpy/advanced/debugging-broadcasting-errors
- SparkCodeHub — Troubleshooting Shape Mismatches:
  https://www.sparkcodehub.com/numpy/data-analysis/troubleshooting-shape-mismatches
- DeepLearning.AI forum — np.sum axis vs keepdims=True:
  https://community.deeplearning.ai/t/dba-np-sum-dtanh-axis-1-or-keepdims-true/297708
- NumPy — bincount docs:
  https://numpy.org/doc/stable/reference/generated/numpy.bincount.html
- copyprogramming — Python lists, mutation, recursion issue:
  https://copyprogramming.com/howto/python-lists-mutation-recursion-issue
- mathspp — Watch out for recursion (Pydon't):
  https://mathspp.com/blog/pydonts/watch-out-for-recursion
- typing spec — Named Tuples:
  https://typing.python.org/en/latest/spec/namedtuples.html
- death.andgravity — NamedTuples in a post-dataclasses world:
  https://death.andgravity.com/namedtuples
- Hitchhiker's Guide to Python — Common Gotchas:
  https://docs.python-guide.org/writing/gotchas/
- scientific-python.org — Best practices for NumPy RNG:
  https://blog.scientific-python.org/numpy/numpy-rng/
- numpy/numpy#15322 — global state for numpy.random:
  https://github.com/numpy/numpy/issues/15322
