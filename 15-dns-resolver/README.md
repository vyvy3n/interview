# Problem 15: DNS Resolver

Recreated from the actual Anthropic Constellation CodeSignal assessment taken 2026-05-09 (the **Python 3 / unittest** track, scored out of 600). You implement a recursive DNS resolver from the root server down, then extend it to handle CNAME chains, missing glue records, NS fallback, cycle detection, batched resolution with caching, and bounded-concurrency batch resolution.

## Why this problem matters

This is a documented, real Anthropic OA — not a synthetic mock. The pattern (single recursive engine that grows feature by feature across stages) is exactly what the Fellows / Constellation track uses. Practicing this gives you authentic muscle memory for:

- Walking a delegated tree (`authority` + `additional` + `answer`) under time pressure
- Handling enum-style status branches (`NOERROR` / `NXDOMAIN` / `REFUSED`)
- Threading a shared cache through a recursive call chain without going global
- Bounding concurrency on top of an existing recursive function

## Files

- `solution.py` — your implementation (`normalize`, `resolve`, `resolve_all`)
- `dns_types.py` — `DNSRecord`, `DNSResponse`, type literals (provided in real test, replicated here)
- `dns_mock.py` — provided `send_query(name, server_ip)` mock (deterministic; raises `QueryLimitExceeded` if you exceed 500 calls per resolve)
- `spec/levelN.md` — the spec for each level (revealed sequentially)
- `test_levelN.py` — standard `unittest` runner; just `python3 test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement in `solution.py`
3. Run `python3 test_level1.py` until all tests pass
4. Move to the next level — repeat

## The 7 levels (high-level only — don't think ahead)

0. **Normalize** — lowercase + ensure trailing dot
1. **Basic delegation** — single NS chain, NOERROR only, with glue record
2. **CNAME records** — restart from root with the alias name; chains can be multi-hop
3. **Missing glue** — recursively resolve the NS's IP first when no glue is provided
4. **NS fallback + error handling** — multiple NS records; on `REFUSED` try next NS, on `NXDOMAIN` give up
5. **Cycle detection** — cap at `max_queries` calls to `send_query` and bail with `None`
6. **Cached batch resolution** — `resolve_all(domains)` with a per-call `(name, server)` cache
7. **Bounded concurrency** — at most `max_workers` calls to `send_query` in flight at any time

## What "Step 0" means here

In the real test, "Step 0 — Normalize" is the warmup. We replicate that as `level1.md` (basic delegation) for naming consistency with the rest of the bank — `normalize()` falls naturally out of Level 1. If you want the real Step-0-isolated drill, run only the `test_normalize_*` tests.

## Calibration

- The real assessment was scored out of 600. The user finished Steps 1–4 cleanly in 90 minutes (with a stuck Step 5 cycle-detection bug) and scored 287/600 — **suggesting Levels 5–7 here are genuinely hard under time pressure**.
- Step 4 is where most of the time goes. The `for ns_record in authority` loop with NS-IP fallback and the empty-additional case is the implementation choke point.
- Step 5 (cycle detection) is a one-line change if you've structured Step 1–4 cleanly with a shared `query_count` counter; it's a 30-minute refactor if you've used recursion without a counter.
- Step 7 (concurrency) is where most candidates run out of time. If you've never written `concurrent.futures` or `asyncio.Semaphore` against a recursive function, expect this to be the hardest part — see `concurrency-primer/` for warmup.

## Differences from the real assessment

- We use `python3 test_levelN.py` instead of `./test.sh N` to match the rest of the bank.
- The real test had a `tests/test_dns.py` single file with `class TestStep0`, `TestStep1`, … We split each step into its own `test_levelN.py` for incremental practice.
- `send_query` raises `QueryLimitExceeded` after 500 calls just like the real mock — useful as a forcing function for cycle handling.
