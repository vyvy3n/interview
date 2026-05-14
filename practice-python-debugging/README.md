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

## The three mocks

Each mock is a self-contained directory: a buggy module + a `test_*.py`
spec + an `ANSWERS.md` key. All three follow the real format — fix the
module, not the tests.

| Mock | Domain | Bugs | Topics exercised |
|---|---|---|---|
| `mock-1-eval-harness/` | label sampling + per-class stats | 7 | `NamedTuple` field order, `RandomState` isolation, `np.bincount` minlength, `np.sum` axis, `np.where` 1-arg, recursion return value, float fractions |
| `mock-2-token-analyzer/` | tokenization + vocab + similarity | 6 | list-comprehension filter, `np.bincount`, `np.where` 1-arg vs 3-arg, broadcasting `(n,)` vs `(n,1)`, NumPy `&` vs `and`, mutable default arg |
| `mock-3-gridworld/` | multi-armed bandit + gridworld DP | 6 | class vs instance attribute, int vs float division, `np.where` div-by-zero guard, `np.sum` axis, `np.min`/`np.max`, recursion boundary case |

19 bugs total across the three, spanning every required topic in the email.

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
