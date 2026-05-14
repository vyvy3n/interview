# Practice — Anthropic Fellows 60-min Python Debugging CodeSignal

Prep for the **second** Fellows assessment: a 60-minute, proctored,
debug-an-existing-codebase test. You're given working-looking Python with a
**failing `unittest` suite**; you fix the **root cause** of each failure
until the suite passes. Finishing early adds a score bonus. You don't need
every test to pass to advance.

See `RESEARCH.md` for the full research outline, bug-archetype catalogue,
and 5-day prep plan. **Honest caveat:** the exact 60-min debugging
assessment isn't publicly attested anywhere — these mocks are built from
the official email's required-topic list crossed with documented Python /
NumPy gotchas, not from leaked questions.

## The seven mocks — a difficulty ladder

Each mock is a self-contained directory: a buggy module + a `test_*.py`
spec + an `ANSWERS.md` key. Every mock follows the real format — fix the
module, not the tests.

**Mocks 1–3 are pdb-onboarding tier** — basic enough to learn the debugger
and the predict→check loop on. **Mocks 4–6 are interview-realistic** —
LLM-domain codebases (tokenizer, attention, sampler) with harder, subtler,
interacting bugs. **Mock 7 is real-assessment difficulty** — bugs in nested
algorithmic logic where the symptom is far from the cause and finding them
needs tracing the intended algorithm, not pattern-matching an archetype.
Climb the ladder in order.

| Mock | Tier | Domain | Bugs | Topics exercised |
|---|---|---|---|---|
| `mock-1-eval-harness/` | onboarding | label sampling + per-class stats | 7 | `NamedTuple` field order, `RandomState` isolation, `bincount` minlength, `sum` axis, `where` 1-arg, recursion return value, float fractions |
| `mock-2-token-analyzer/` | onboarding | tokenization + vocab + similarity | 6 | list-comp filter, `bincount`, `where` 1-arg vs 3-arg, broadcasting `(n,)` vs `(n,1)`, `&` vs `and`, mutable default arg |
| `mock-3-gridworld/` | onboarding | multi-armed bandit + gridworld DP | 6 | class vs instance attr, int vs float division, `where` div-by-zero guard, `sum` axis, `min`/`max`, recursion boundary case |
| `mock-4-bpe-tokenizer/` | **interview** | BPE tokenizer: vocab, merges, encode/decode | 7 | vocab off-by-one, `NamedTuple` positional swap, **recursion loop-range off-by-one**, list-comp `dict.get`, `bincount` minlength, `where`/`nonzero`, float division |
| `mock-5-attention/` | **interview** | scaled dot-product attention + masking | 7 | **softmax numerical stability (overflow→nan)**, `keepdims` broadcasting, `1/sqrt(d)` scaling, `tril` offset, `where` 3-arg branch order, `(B,S)` vs `(B,S,S)` broadcast, `sum` axis |
| `mock-6-sampler/` | **interview** | temperature / top-k / top-p / generation | 8 | temperature formula, `argsort` direction, renormalization, `max` vs `argmax`, `nonzero`, `RandomState` re-seed, recursion base-case off-by-one, perplexity formula |
| `mock-7-beam-search/` | **hardest** | beam-search decoder | 6 | **nested algorithmic logic** — structural (no global prune; token-list aliasing), missing-logic (no finished-beam guard; raw vs length-normalized pick), subtle indexing deep in a loop, algorithm-understanding (`prune` sort direction). Bugs interact; symptom far from cause. Self-teaching docstrings + tests. |

**46 bugs total.** Mocks 1–3 cover every required topic gently; mocks 4–6
re-hit them in realistic, harder, LLM-flavored code where bugs sit in shared
helpers and cascade; mock 7 is the closest to a real "fix this codebase"
assessment — read its docstrings and test file to learn beam search from
scratch.

**Worked reference:** `mock-1-eval-harness/eval_harness_solution.py` is a
fully-fixed version of mock 1 — all 16 tests pass. Every mock's `ANSWERS.md`
documents every bug, how it surfaces, and debugging notes.

## How to practice

```bash
cd practice-python-debugging/mock-1-eval-harness

# 1. Read the test file FIRST — it's the spec.
cat test_eval_harness.py

# 2. Run the suite, read every failure.
python -m unittest test_eval_harness -v

# 3. Fix the root cause in eval_harness.py. Re-run. Repeat.
#    Debug with pdb:  python -m pdb -m unittest test_eval_harness
#    or just drop  breakpoint()  into the module.

# 4. When green (or time's up), check your work:
cat ANSWERS.md

# 5. Reset to practice again:
git checkout eval_harness.py
```

**Recommended:** set a real 60-minute timer per mock. Target split:
read all test names (3 min) → run suite, read all failures (5 min) →
fix-and-rerun loop (~50 min) → buffer (2 min). Fix the most
load-bearing / most-failing bugs first.

## Strategy reminders from the official email

- **The test suite is the final word on requirements.** If behavior isn't
  checked by a test, it's not a bug you need to fix.
- **Don't worry about edge cases with no tests.** This *inverts* the advice
  for the 90-min general round — here, scope is exactly the test suite.
- **Run tests early and often.** Re-run after every fix.
- A failing test you can't crack quickly: skip it, come back. You don't
  need 100%.

## Tooling to have ready

- `python -m pdb -m unittest test_x` — drop into pdb; or `breakpoint()` in code.
- `pdb` muscle memory: `b file:line`, `c`, `n`, `s`, `p`/`pp var`, `w`,
  `u`/`d`, `ll`, `!expr`.
- `pip install pdbpp` for the nicer interface — but have a plan B with bare
  `pdb` in case the test environment doesn't have it.
- Read `RuntimeWarning`s — NumPy prints them to stderr and they often point
  straight at the bug line.

## A note on `NamedTuple`

The email says `collections.NamedTuple`. There is no such name — `collections`
has the `namedtuple` *function*; `typing` has the `NamedTuple` *class*. These
mocks use the modern `typing.NamedTuple` class syntax. Be ready to recognize
all three: `typing.NamedTuple`, `collections.namedtuple`, and
`dataclasses.dataclass`.
