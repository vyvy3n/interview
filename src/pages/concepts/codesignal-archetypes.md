---
layout: ../../layouts/Layout.astro
title: CodeSignal Archetypes
---

# CodeSignal Archetypes

> Every Anthropic/Karat ICF problem is a dispatch loop with a state machine inside — learn the shape once, map any domain onto it.

## When you'll see this

- Anthropic OA (4-level, `solution(queries)` function)
- Anthropic Fellows / Research Engineer OA (same shape, harder ops at L3-L4)
- Karat live interviews (4 or 6 levels, often 90 min)
- OpenAI contractor screens (same query-list pattern, different domain)
- Coinbase / Meta ICF-format assessments

## The canonical shape

**4-level (function-based):** one function `solution(queries: list[list[str]]) -> list[str]` that you extend across all four levels. You never rewrite it from scratch — you add `elif` branches and new state fields.

**6-level (class-based):** one class (e.g. `TaskScheduler`, `KVStore`) with methods. L1-L4 are synchronous; L5-L6 add `threading` or `asyncio`. Same "extend, don't rewrite" discipline.

Both shapes share the invariant: **single state that evolves across levels**. The design you choose at L1 either saves or kills you at L4.

## The level-progression skeleton

- **L1:** basic CRUD — create / read / delete one entity. No aggregation, no time.
- **L2:** aggregate query — top-K, sum, count, list-by-x. Sorting and formatting matter.
- **L3:** time / users dimension — TTL, scheduled events, per-user quotas, lazy refill.
- **L4:** complex compose — merge, fork, snapshot/restore, bulk invalidation.
- **L5:** concurrency introduced — `threading.Lock` or `asyncio.Lock` around all mutations.
- **L6:** hardest concurrency compose — atomic compound ops, cancellation propagation, event-based blocking.

## Template: dispatch loop (4-level, list-of-list-of-strings)

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Account:
    balance: int = 0
    outgoing: int = 0
    scheduled: list = field(default_factory=list)

def solution(queries: list[list[str]]) -> list[str]:
    accounts: dict[str, Account] = {}
    payment_counter = 0
    out = []

    for q in queries:
        cmd, *args = q
        ts = int(args[0])

        # Fire deferred events BEFORE the current command (L3+ pattern)
        _advance_time(accounts, ts)

        if cmd == "CREATE_ACCOUNT":
            _, acct_id = args
            if acct_id in accounts:
                out.append("false")
            else:
                accounts[acct_id] = Account()
                out.append("true")

        elif cmd == "DEPOSIT":
            _, acct_id, amount = args
            if acct_id not in accounts:
                out.append("")
            else:
                accounts[acct_id].balance += int(amount)
                out.append(str(accounts[acct_id].balance))

        elif cmd == "PAY":
            _, acct_id, amount = args
            amt = int(amount)
            if acct_id not in accounts or accounts[acct_id].balance < amt:
                out.append("")
            else:
                accounts[acct_id].balance -= amt
                accounts[acct_id].outgoing += amt
                out.append(str(accounts[acct_id].balance))

        # elif cmd == "TRANSFER": ...
        # elif cmd == "TOP_SPENDERS": ...
        # elif cmd == "SCHEDULE_PAYMENT": ...
        # elif cmd == "MERGE_ACCOUNTS": ...

        else:
            out.append("")

    return out


def _advance_time(accounts: dict, ts: int) -> None:
    """Fire all scheduled payments due at or before ts. Call at top of every loop iter."""
    due = sorted(
        [p for acct in accounts.values() for p in acct.scheduled
         if not p["fired"] and not p["cancelled"] and p["execute_at"] <= ts],
        key=lambda p: (p["execute_at"], p["seq"])
    )
    for p in due:
        p["fired"] = True
        owner = accounts.get(p["owner"])
        if owner and owner.balance >= p["amount"]:
            owner.balance -= p["amount"]
            owner.outgoing += p["amount"]
```

## Template: class + methods (6-level)

```python
import threading
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Task:
    task_id: str
    duration: int
    priority: int = 0
    seq: int = 0                         # submission order for tie-breaking
    status: str = "pending"
    deps: list[str] = field(default_factory=list)
    event: threading.Event = field(default_factory=threading.Event)

class TaskScheduler:
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._seq = 0
        self._lock = threading.Lock()
        self._workers: list[threading.Thread] = []
        self._stop_event = threading.Event()

    # --- L1: basic lifecycle ---
    def submit_task(self, task_id: str, duration: int) -> bool:
        with self._lock:
            if task_id in self._tasks:
                return False
            self._seq += 1
            self._tasks[task_id] = Task(task_id, duration, seq=self._seq)
            return True

    def get_status(self, task_id: str) -> str:
        with self._lock:
            t = self._tasks.get(task_id)
            return t.status if t else ""

    def complete_task(self, task_id: str) -> bool:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t or t.status != "pending":
                return False
            t.status = "completed"
            t.event.set()
            return True

    # --- L2: reporting ---
    def list_by_status(self, status: str) -> list[str]:
        with self._lock:
            return sorted(t.task_id for t in self._tasks.values() if t.status == status)

    # --- L3: priorities ---
    def get_next_task(self) -> str:
        with self._lock:
            pending = [t for t in self._tasks.values() if t.status == "pending"]
            if not pending:
                return ""
            best = min(pending, key=lambda t: (-t.priority, t.seq))
            return best.task_id

    # --- L4: dependencies ---
    def get_next_runnable(self) -> str:
        with self._lock:
            runnable = [
                t for t in self._tasks.values()
                if t.status == "pending"
                and all(self._tasks.get(d, Task("", 0, status="")).status == "completed"
                        for d in t.deps)
            ]
            if not runnable:
                return ""
            return min(runnable, key=lambda t: (-t.priority, t.seq)).task_id

    # --- L5: workers ---
    def start_workers(self, count: int) -> None:
        for _ in range(count):
            w = threading.Thread(target=self._worker_loop, daemon=True)
            w.start()
            self._workers.append(w)

    def _worker_loop(self) -> None:
        import time
        while not self._stop_event.is_set():
            with self._lock:
                task_id = self.get_next_runnable()  # must be re-entrant-safe
                if task_id:
                    self._tasks[task_id].status = "running"
            if task_id:
                duration = self._tasks[task_id].duration
                time.sleep(duration)
                with self._lock:
                    self._tasks[task_id].status = "completed"
                    self._tasks[task_id].event.set()
            else:
                time.sleep(0.01)

    def stop_workers(self) -> None:
        self._stop_event.set()
        for w in self._workers:
            w.join()

    # --- L6: cancellation + waiting ---
    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t or t.status != "pending":
                return False
            t.status = "cancelled"
            t.event.set()
            # propagate to dependents
            for other in self._tasks.values():
                if task_id in other.deps and other.status == "pending":
                    self.cancel_task(other.task_id)  # recursive under same lock — careful!
            return True

    def wait_for_completion(self, task_id: str, timeout: float = None) -> str:
        t = self._tasks.get(task_id)
        if not t:
            return ""
        t.event.wait(timeout=timeout)
        return t.status
```

*Test file pattern (unittest, L5+):*

```python
import unittest, threading, time
from solution import TaskScheduler

class TestL5Workers(unittest.TestCase):
    def test_worker_completes_task(self):
        s = TaskScheduler()
        s.submit_task("t1", duration=0)
        s.start_workers(1)
        time.sleep(0.1)
        self.assertEqual(s.get_status("t1"), "completed")
        s.stop_workers()
```

## Template: state-evolution helper (per-entity dataclass)

How the `Account` object grows across levels — the typical evolution pattern:

```python
# L1: start minimal — just a balance
accounts: dict[str, int] = {}

# L2 forces refactor: add outgoing tracking (parallel dict = pain)
# Collapse into a dataclass NOW to avoid two dicts drifting apart
@dataclass
class Account:
    balance: int = 0
    outgoing: int = 0           # added at L2

# L3: add scheduled payments to the same object
@dataclass
class Account:
    balance: int = 0
    outgoing: int = 0
    scheduled: list = field(default_factory=list)   # added at L3

# L4: no new fields needed — MERGE_ACCOUNTS walks scheduled list and re-keys
# Rule: one dataclass per entity, add fields as levels demand, never parallel dicts
```

Parallel dicts (`balances`, `outgoing`, `scheduled`) fall out of sync when you add MERGE or RESTORE. A single dataclass per entity keeps everything co-located.

## Template: fire-on-every-query helper (deferred events / scheduled / TTL cleanup)

This pattern appears in every problem that has L3 time-based side-effects:

```python
def solution(queries):
    state = {}
    events: list[dict] = []   # scheduled payments, or TTL expiries, or anything time-driven

    for q in queries:
        cmd, *args = q
        ts = int(args[0])

        # THE PATTERN: advance time BEFORE the command runs
        _advance_time(state, events, ts)

        if cmd == "SCHEDULE_PAYMENT":
            # register a future event
            events.append({"execute_at": ts + int(args[3]), "owner": args[1], ...})
        elif cmd == "GET":
            # TTL check is also handled in _advance_time (expired entries removed from state)
            ...

    return out


def _advance_time(state, events, current_ts):
    """
    Bank L3: fire scheduled payments whose execute_at <= current_ts
    DB  L3:  remove TTL entries whose expiry <= current_ts
    Rate limiter L3: refill token buckets based on elapsed time since last_seen_ts
    """
    # Example — scheduled payment firing:
    due = [e for e in events if e["execute_at"] <= current_ts and not e.get("done")]
    due.sort(key=lambda e: (e["execute_at"], e["seq"]))
    for e in due:
        e["done"] = True
        owner = state.get(e["owner"])
        if owner and owner.balance >= e["amount"]:
            owner.balance -= e["amount"]
            owner.outgoing += e["amount"]
```

For TTL-only problems (DB, Prompt Cache), you can skip a separate events list and just check `expiry_ts <= current_ts` on every read — "lazy expiry" instead of "eager expiry". Both work; lazy is simpler to implement under time pressure.

---

## The 8 archetype problem domains

### 1. Bank / transaction system

Per-account ledger with deferred payments and account merging. The most-cited Anthropic prompt.

- **Reported at:** Anthropic (most-cited), Karat
- **L1 ops:** `CREATE_ACCOUNT`, `DEPOSIT`, `PAY`
- **L2 ops:** `TRANSFER`, `TOP_SPENDERS` (descending outgoing, alphabetical tiebreak)
- **L3 ops:** `SCHEDULE_PAYMENT` (returns `paymentN` id), `CANCEL_PAYMENT` (fires due payments first)
- **L4 ops:** `MERGE_ACCOUNTS` (balance + outgoing + pending payments all transfer; absorbed account deleted)
- **Data structure trick:** store absolute `execute_at` timestamp on each scheduled payment, fire all `<= ts` at top of every handler sorted by `(execute_at, seq)`. For MERGE, walk `id2.scheduled`, re-key owner to `id1`, then delete `id2` from every dict.

### 2. In-memory key-value-field database

Two-level dict `{key: {field: value}}` with optional TTL and snapshot semantics.

- **Reported at:** Anthropic
- **L1 ops:** `SET` (returns `""`), `GET`, `DELETE` (returns `"true"/"false"`)
- **L2 ops:** `SCAN` (all fields at key, alphabetically), `SCAN_BY_PREFIX`
- **L3 ops:** `SET_WITH_TTL`, `UPDATE_TTL` — expiry check (`ts >= expiry`) gates every read/delete/scan
- **L4 ops:** `BACKUP` (snapshot with remaining TTL, not absolute expiry), `RESTORE` (re-anchors TTL to restore ts)
- **Data structure trick:** store `(value, expiry_ts | None)` per `(key, field)`. At BACKUP, compute `remaining = expiry - ts`; at RESTORE, set `new_expiry = restore_ts + remaining`. This way restore works correctly regardless of when it's called.

### 3. File system (mini Dropbox)

Flat global file namespace, prefix search, per-user ownership and quota, compression.

- **Reported at:** Anthropic, Karat
- **L1 ops:** `FILE_UPLOAD` (no overwrite), `FILE_GET` (returns size), `FILE_COPY` (new name, same size)
- **L2 ops:** `FILE_SEARCH` (prefix, top-10 by size desc then name asc)
- **L3 ops:** `USER_REGISTER`, `USER_UPLOAD` (quota enforcement, returns remaining capacity), `USER_GET`, `USER_COPY`, `USER_SEARCH`
- **L4 ops:** `COMPRESS_FILE` (halve size, remember original; one-way until decompressed), `DECOMPRESS_FILE`, `USER_MERGE` (fail if name conflict)
- **Data structure trick:** single flat `files: dict[str, FileRecord]` for all files (admin + users). `FileRecord` holds `owner`, `size`, `original_size`, `compressed`. User's `used` bytes = sum of owned file sizes. Keep `used` as a cached field on the `User` dataclass, not recomputed on every query.

### 4. Cloud storage system

Per-user quota + file sharing + backup/restore. Distinct from File System: focuses on sharing and ownership transfer.

- **Reported at:** Anthropic
- **L1 ops:** `ADD_USER` (capacity), `UPLOAD_FILE` (quota check, returns remaining)
- **L2 ops:** `GET_FILE_SIZE`, `GET_LARGEST_FILES` (top-K across all users), `GET_USER_USAGE`
- **L3 ops:** `SHARE_FILE` with multiple recipients — file stays in owner's quota, recipients can access it
- **L4 ops:** `BACKUP` (snapshot of user's file list), `RESTORE`, `TRANSFER_OWNERSHIP` (move file + quota to another user)
- **Data structure trick:** separate `users: dict[str, User]` and `files: dict[str, File]`. `File` has `owner` and `shared_with: set`. Sharing only changes `shared_with` — owner's `used` is unchanged. TRANSFER_OWNERSHIP updates `file.owner` and adjusts both users' `used` in one step.

### 5. LLM request router (KV-cache aware)

GPU fleet manager with load-aware routing, per-GPU LRU prefix caches, failure handling.

- **Reported at:** Anthropic (infra/research roles)
- **L1 ops:** `REGISTER_GPU` (capacity), `ROUTE_REQUEST` (returns assigned `gpu_id`, picks least-loaded), `COMPLETE_REQUEST` (frees slot)
- **L2 ops:** `GPU_LOAD` (returns `"active/capacity"`), `TOP_BUSIEST` (fleet ranking)
- **L3 ops:** `ROUTE_REQUEST_WITH_PREFIX` (prefer GPU with prefix cached, fall back to least-loaded; each GPU has LRU cache of 5 prefixes)
- **L4 ops:** `FAIL_GPU` (evict requests, re-route in `request_id` alphabetical order with prefix affinity), `RECOVER_GPU` (empty cache, original capacity)
- **Data structure trick:** per-GPU LRU cache is just an `OrderedDict` with maxlen 5 — `cache.move_to_end(prefix)` on hit, `cache.popitem(last=False)` on eviction. Track `request_id → (gpu_id, prefix)` so FAIL_GPU can re-route with the original prefix.

### 6. LLM prompt cache

KV cache for prompt→response pairs with hit tracking, LRU eviction, and prefix matching.

- **Reported at:** Anthropic
- **L1 ops:** `CACHE_PUT` (returns `""`), `CACHE_GET` (returns response or `""`), `CACHE_DELETE`
- **L2 ops:** `HIT_COUNT` (per-prompt hit counter), `TOP_K_HOT` (most-hit entries)
- **L3 ops:** `CACHE_PUT_WITH_TTL`, `SET_CAPACITY` (LRU eviction — evict entry with oldest `last_access` when over limit)
- **L4 ops:** `PREFIX_LOOKUP` (find longest cached prompt that is a prefix of the query), `INVALIDATE_PREFIX` (bulk delete all entries whose prompt starts with prefix)
- **Data structure trick:** store `(response, hits, last_access_ts, expiry_ts | None)` per prompt. For `PREFIX_LOOKUP`, iterate all live entries and pick the longest that is a true string prefix — no trie needed at interview scale. For LRU, don't use `OrderedDict`; instead track `last_access` as a timestamp and sort on eviction.

### 7. LLM rate limiter (token bucket)

Per-API-key token bucket with continuous refill, top-K consumers, and tier/key merging.

- **Reported at:** Anthropic
- **L1 ops:** `REGISTER_KEY` (max_tokens), `CONSUME` (deduct if sufficient, return remaining or `""`), `GET_REMAINING`
- **L2 ops:** `TOTAL_CONSUMED` (cumulative across all successful consumes), `TOP_K_CONSUMERS`
- **L3 ops:** `SET_REFILL_RATE` (tokens/second) — lazy refill: on every query touching a key, compute `tokens_to_add = (current_ts - last_ts) * rate`, clamp to `max_tokens`, update balance before acting
- **L4 ops:** `UPGRADE_TIER` (new max + rate; re-clamp current balance to new max), `MERGE_KEYS` (combine balance, max, rate, total_consumed; absorbed key deleted)
- **Data structure trick:** lazy refill means you don't need a background thread. Store `last_seen_ts` per key. At the top of every command that touches a key, run `_refill(key, ts)` before reading/writing. This is exactly the same `_advance_time` pattern as scheduled payments, just per-entity instead of global.

### 8. LLM conversation manager

Multi-user chatbot session store with token budgets, FIFO truncation, and fork/merge.

- **Reported at:** Anthropic, Karat
- **L1 ops:** `CREATE_CONVERSATION` (conv_id, user_id), `ADD_MESSAGE` (role, text, tokens), `GET_MESSAGE_COUNT`
- **L2 ops:** `TOP_K_ACTIVE` (by message count desc, conv_id asc for ties), `LIST_USER_CONVERSATIONS`
- **L3 ops:** `SET_CONTEXT_LIMIT` (enforce immediately via FIFO drop from front), `ADD_MESSAGE_WITH_BUDGET` (drop oldest until new message fits; reject if message tokens > limit)
- **L4 ops:** `FORK_CONVERSATION` (deep copy, new conv_id), `MERGE_CONVERSATIONS` (interleave by per-message ts, surviving conv wins ties; re-enforce budget if set)
- **Data structure trick:** store each message as `{"role": ..., "text": ..., "tokens": ..., "ts": ts}`. MERGE is a merge-sort by `msg["ts"]` then re-truncate from front. FORK is `copy.deepcopy(conv)` with a new ID — don't share the message list reference.

---

## Universal gotchas across all archetypes

- **Stringify everything** — return `str(balance)`, `"true"/"false"`, `""` for error/missing. Never return a bare int or `None`.
- **Timestamps are string inputs** — always `int(ts)` before arithmetic; they look numeric but arrive as strings.
- **Empty string `""` is the universal error sentinel** — not `"null"`, not `"-1"`, not `"error"`. When in doubt, return `""`.
- **Failed operations must not mutate state** — a failed PAY must not decrement balance; a failed TRANSFER must touch neither account; a failed MERGE must leave both accounts intact.
- **Strings in the output list must align query-by-query** — the return list is the same length as the input list, in the same order. Missing an `out.append(...)` in any branch shifts every subsequent result.
- **Don't pre-design for unknown future levels** — L1 code should not anticipate L4 ops. Over-engineering wastes time and adds bugs. Refactor when the new level *forces* you to.
- **Refactor early within a level, not in the middle of L4 panic** — if L2 makes a flat-dict design untenable, refactor at the start of L2, not when L4 MERGE drops on you.
- **TOP_K with n > entity count** — return all entities, not an error. Never pad with empty strings.
- **Tie-breaking rules are exact** — re-read the spec. Usually: value descending, then ID/name alphabetically ascending. Sort key: `(-value, name)`.
- **`"paymentN"` IDs use numeric order, not lex order** — `payment2` < `payment10` numerically but `"payment10" < "payment2"` lexicographically. Parse the integer suffix for sort: `int(pid.replace("payment",""))`.
- **For 6-level: lock everything in concurrent levels, even reads** — `get_status` under `threading.Lock` prevents stale reads during concurrent writes. No lock-free shortcuts.
- **`asyncio.Lock` must be created inside the async context** — create it in `__init__` or `__aenter__`, not at module level, to avoid event loop binding errors.

## Universal techniques across all archetypes

- **Per-entity dataclass at L2 onwards** — move from `dict[str, int]` to `dict[str, MyEntity]` as soon as you need a second field per entity. Avoids the parallel-dicts-fall-out-of-sync failure mode.
- **Sort by tuple key** — `sorted(entities, key=lambda e: (-e.value, e.name))` handles descending-value + ascending-name in one expression. No custom comparator needed.
- **Top-K via `sorted(...)[:k]`** — for K up to a few hundred at interview scale, this is faster to write and sufficient in practice. Only use `heapq.nsmallest/nlargest` if the problem explicitly requires it.
- **Store absolute `execute_at` / `expiry_ts`, fire with `<= ts`** — simpler than managing deltas. Exception: BACKUP/RESTORE must store remaining TTL so RESTORE can re-anchor.
- **`_advance_time(ts)` helper called at the top of every loop iteration** — centralizes all time-driven side-effects. One function, called before every `if/elif` chain. Never duplicated per-command.
- **Lazy refill for token buckets** — store `last_seen_ts` per key, compute refill `= (ts - last_ts) * rate` on every touch. No background thread needed. Same pattern as `_advance_time` but per-entity.
- **MERGE pattern: walk once, mutate in place, then delete** — for any merge op: transfer `id2`'s fields onto `id1` in a single pass, re-key any sub-objects (e.g. payments), then `del lookup[id2]`. One loop, no copies.
- **FORK pattern: `copy.deepcopy`** — for conversation/snapshot forks. Cheap at interview scale; avoid sharing list references between parent and fork.
- **`defaultdict(dict)` for nested state** — `db = defaultdict(dict)` lets you `db[key][field] = value` without pre-initializing the inner dict.
- **Mutating a dict while iterating it** — always `list(d.keys())` or `list(d.items())` before a loop that might delete entries. `for k in list(d):` is the safe idiom.
- **Return type for "list all" operations** — when the filtered set is empty, return `""` (empty string), not `[]` or `"[]"`. Read the spec, but this is the default.

---

## Practice (in-repo problems)

- **Problem 01 — Bank Transactions** — full 4-level bank: CREATE_ACCOUNT/DEPOSIT/PAY, TRANSFER + TOP_SPENDERS, SCHEDULE_PAYMENT + CANCEL_PAYMENT (deferred payments with fire-before-query timing), MERGE_ACCOUNTS (balance + outgoing + pending all consolidate). *Insight:* refactor to a per-Account dataclass at L2 — the scheduled list and outgoing field land cleanly on it, and MERGE_ACCOUNTS becomes a single-pass walk. [01-bank-transactions/](https://github.com/vyvy3n/interview/blob/main/01-bank-transactions/solution.py)

- **Problem 02 — In-Memory Database** — two-level dict SET/GET/DELETE, SCAN/SCAN_BY_PREFIX with alphabetical field ordering, TTL expiry (half-open interval: expired at `ts >= expiry`), BACKUP (stores remaining TTL) + RESTORE (re-anchors TTL). *Insight:* lazy expiry is sufficient — check `ts >= expiry_ts` on every read/delete/scan without a cleanup pass. Store `None` for no-TTL entries to distinguish from TTL=0. [02-in-memory-db/](https://github.com/vyvy3n/interview/blob/main/02-in-memory-db/solution.py)

- **Problem 03 — File System** — flat global namespace FILE_UPLOAD/GET/COPY, FILE_SEARCH top-10 by size then name, per-user USER_UPLOAD with quota and remaining-capacity return, COMPRESS_FILE (floor-halve, track original) + DECOMPRESS_FILE + USER_MERGE (fail on name conflict). *Insight:* keep a single `files` dict for all files (admin and user-owned) so FILE_UPLOAD and USER_UPLOAD share the same namespace check. Cache `user.used` as a field — don't recompute by summing file sizes on every op. [03-file-system/](https://github.com/vyvy3n/interview/blob/main/03-file-system/solution.py)

- **Problem 04 — Cloud Storage** — per-user ADD_USER with capacity, UPLOAD_FILE with quota, GET_LARGEST_FILES fleet ranking, SHARE_FILE (shared files count only against owner's quota), BACKUP/RESTORE per user + TRANSFER_OWNERSHIP. *Insight:* sharing is just a `shared_with: set` on the File object — the owner's `used` bytes don't change on share. TRANSFER_OWNERSHIP adjusts both users' `used` by the file's size in one step. [04-cloud-storage/](https://github.com/vyvy3n/interview/blob/main/04-cloud-storage/solution.py)

- **Problem 05 — LLM Request Router** — REGISTER_GPU/ROUTE_REQUEST/COMPLETE_REQUEST (least-loaded routing), GPU_LOAD/TOP_BUSIEST observability, ROUTE_REQUEST_WITH_PREFIX with per-GPU 5-slot LRU prefix cache (prefer cached GPU, fall back to least-loaded), FAIL_GPU (re-route in-flight requests alphabetically with prefix affinity) + RECOVER_GPU. *Insight:* use `collections.OrderedDict` as LRU cache with `move_to_end` on hit and `popitem(last=False)` on eviction. Store `request_id → (gpu_id, prefix)` from L3 onward so FAIL_GPU can re-route with the original prefix. [05-llm-request-router/](https://github.com/vyvy3n/interview/blob/main/05-llm-request-router/solution.py)

- **Problem 06 — LLM Prompt Cache** — CACHE_PUT/GET/DELETE, HIT_COUNT + TOP_K_HOT (hits descending, prompt asc for ties), CACHE_PUT_WITH_TTL + SET_CAPACITY with LRU eviction on oldest `last_access`, PREFIX_LOOKUP (longest cached prompt that is a string prefix of query) + INVALIDATE_PREFIX (bulk delete). *Insight:* for PREFIX_LOOKUP, iterate all live entries and find the longest that passes `query.startswith(cached_prompt)` — no trie needed. LRU eviction: track `last_access_ts` per entry, evict `min(live_entries, key=lambda e: e.last_access)` when over capacity. [06-llm-prompt-cache/](https://github.com/vyvy3n/interview/blob/main/06-llm-prompt-cache/solution.py)

- **Problem 07 — LLM Rate Limiter** — REGISTER_KEY/CONSUME/GET_REMAINING (token bucket, deny if insufficient), TOTAL_CONSUMED + TOP_K_CONSUMERS, SET_REFILL_RATE with lazy per-key refill `(ts - last_ts) * rate` before every operation, UPGRADE_TIER (new max + rate, re-clamp balance) + MERGE_KEYS (combine everything, delete absorbed key). *Insight:* lazy refill is the same `_advance_time` pattern applied per-entity. Store `last_seen_ts` on each key's dataclass and call `_refill(key, ts)` at the top of every branch that touches that key. [07-llm-rate-limiter/](https://github.com/vyvy3n/interview/blob/main/07-llm-rate-limiter/solution.py)

- **Problem 08 — LLM Conversation Manager** — CREATE_CONVERSATION/ADD_MESSAGE/GET_MESSAGE_COUNT, TOP_K_ACTIVE + LIST_USER_CONVERSATIONS, SET_CONTEXT_LIMIT (immediate FIFO truncation) + ADD_MESSAGE_WITH_BUDGET (reject if tokens > limit, else drop oldest until fits), FORK_CONVERSATION (deep copy) + MERGE_CONVERSATIONS (merge-sort by per-message ts, re-enforce budget). *Insight:* store `ts` on every message at add-time — MERGE needs it for interleaving. FORK is `copy.deepcopy`; don't share the message list between parent and child. [08-llm-conversation-manager/](https://github.com/vyvy3n/interview/blob/main/08-llm-conversation-manager/solution.py)

- **Problem 09 — Concurrent Task Scheduler** — 6-level class: submit/get_status/complete, list/count by status, priority queue (higher int = higher priority, submission order breaks ties), dependency DAG with cycle detection, `threading` worker pool (lock all mutations), cancellation with dependency propagation + `threading.Event` blocking wait. *Insight:* at L5, the worker thread must release the lock while `time.sleep(duration)` runs — acquire to pick task, release, sleep, acquire again to mark complete. At L6, cancel propagation is recursive — guard against cycles in the dependency graph. [09-concurrent-task-scheduler/](https://github.com/vyvy3n/interview/blob/main/09-concurrent-task-scheduler/solution.py)

- **Problem 10 — Thread-Safe Key-Value Store** — 6-level class: sync put/get/delete, bulk ops and prefix queries, TTL expiry with timestamps, LRU capacity cap, async concurrent access with `asyncio.Lock` (aget/aput/adelete), atomic compound ops: `acompare_and_set`, `aget_and_set`, `aincrement` (all hold lock for entire read-modify-write). *Insight:* create `asyncio.Lock()` in `__init__` — do NOT create it at module or class level outside an async context or it binds to the wrong event loop. Compound ops must hold the lock for the full CAS sequence, not just the read or just the write. [10-thread-safe-keyvalue/](https://github.com/vyvy3n/interview/blob/main/10-thread-safe-keyvalue/solution.py)
