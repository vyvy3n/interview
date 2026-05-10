# Problem 15: DNS Resolver — real Anthropic Constellation OA

Reconstructed from screenshots of the actual Anthropic Constellation CodeSignal taken 2026-05-09 (Python 3 / unittest, scored out of 600). 7 progressive steps from a basic delegation walk through CNAME chains, missing-glue recursion, NS fallback, cycle detection, cached batch resolution, and bounded-concurrency parallel resolution.

> **This problem mirrors the assessment's actual file layout** (`tests/test_dns.py`, `./test.sh N`, single `dns_exercise.py` to fill in). Other problems in this bank use a per-level `test_levelN.py` format — this one doesn't, by design.

## Files (matches the assessment)

| File | Purpose |
|---|---|
| `dns_exercise.py` | **Starter** — the file you fill in. `normalize`, `resolve`, `resolve_all` with `# TODO` blocks. |
| `solution.py` | Reference solution (the worked-out version of `dns_exercise.py`). Tests import from here so they pass out of the box. |
| `dns_types.py` | Provided types — `DNSRecord`, `DNSResponse`, `ServerIP`, `ZoneName`, `RecordType`. **DO NOT MODIFY**. |
| `dns_mock.py` | Provided mock — named server-IP constants (`ROOT`, `COM`, `ANTHROPIC_NS`, …), the simulated internet (`ZONES`), `send_query()`, and the test-only call-log / in-flight tracker. **DO NOT MODIFY**. |
| `tests/test_dns.py` | The test suite — one `TestStepN` class per step. Each test calls `_resolve_and_log(domain)` and asserts both the IP result *and* the exact sequence of `send_query` calls. |
| `test.sh` | `./test.sh N` runs all `TestStepN` tests via pytest. `./test.sh` runs every step. |
| `spec/levelN.md` | The verbatim Step N description from the assessment (revealed sequentially). |

## Workflow (matches the assessment)

1. Open `dns_exercise.py` (the starter)
2. Read `spec/level1.md`
3. Implement until `./test.sh 1` passes
4. Move to `spec/level2.md` → implement → `./test.sh 2` → repeat through Step 7

If you want to see the worked-out version, check `solution.py`. The tests import from `solution`, so the suite passes out of the box — to actually practice, point the imports at `dns_exercise` (or just rename `solution.py` to `dns_exercise.py` after backing up the starter).

## The 7 levels (high-level — don't think ahead)

| Step | What's new |
|---|---|
| **0** | `normalize()` — lowercase + ensure trailing dot |
| **1** | Basic delegation: root → TLD → authoritative, with glue, `NOERROR` only |
| **2** | `CNAME` answers — restart from root with the alias name; chains can be multi-hop |
| **3** | Missing glue — recursively resolve the NS's IP first |
| **4** | Multiple NS records + `NXDOMAIN` (give up) / `REFUSED` (try next NS) |
| **5** | Cycle detection — give up after `max_queries` calls to `send_query` |
| **6** | `resolve_all()` with per-call `(name, server)` cache — `NXDOMAIN`/`REFUSED` cached too; cache hits count against per-domain `max_queries` |
| **7** | Bounded concurrency — at most `max_workers` calls in flight; in-flight queries from another domain are awaited rather than duplicated |

## Calibration

- The user finished Steps 1–4 cleanly in 90 minutes (with a stuck Step 5 cycle-detection bug) and scored **287/600**. Levels 5–7 are genuinely hard under time pressure.
- Step 4 is the implementation choke point — the `for ns_record in authority` loop with NS-IP fallback and the empty-additional case eats time.
- Step 5 is one line if Step 1–4 share a `query_count` counter; it's a 30-minute refactor if you've used unstructured recursion.
- Step 7 (single-flight in-flight dedup) requires either `concurrent.futures.Future` registry tracking or `asyncio` with a lock around the cache. If neither pattern is muscle-memory, expect this to be the hardest part — see `concurrency-primer/` for warmup.

## Differences from the real assessment

- Names of internal helpers (`_assert_log_equal`, `_resolve_and_log`) match what was visible in the screenshots; their bodies are reasonable reconstructions.
- The simulated internet topology (`ZONES`) is reconstructed from the named server constants visible in the screenshots and the test names that appeared in error traces. The exact set of test cases per step in the real assessment is larger than what's here — these tests cover every feature each spec bullet calls out.
- Real `send_query` raises `QueryLimitExceeded` after 500 calls; we match that.
