---
layout: ../../layouts/Layout.astro
title: State Serialization
---

# State Serialization

> Save just enough state to resume; never serialize objects you can re-derive.

## When to use

- Resumable iterators (pause mid-stream, hand off state dict, restart in fresh process)
- Snapshot / BACKUP + RESTORE for in-memory databases and KV stores
- Distributed checkpoints: workers die, coordinator re-issues state dict to replacement
- OpenAI Resumable Multi-File Iterator — explicit get_state / set_state requirement
- OpenAI Versioned KV Store — binary serialization of records to a single byte blob

## What "state" actually is

- Primitives, indexes, offsets, dicts/lists of primitives — **YES, serialize these**
- File handles, iterators, sockets, locks, threads, open DB connections — **NO, re-derive from primitives**
- The mental model: state is what you'd write to disk; re-derivable runtime objects are **not** state

## The save / restore contract

- `get_state() -> dict` — return only primitives + lists/dicts of primitives; no live objects
- `set_state(state: dict) -> None` — rebuild all runtime objects from those primitives
- `step()` / `next()` — mutates internal state; must be deterministic from current state
- Round-trip invariant: `a.set_state(b.get_state())` produces an instance equivalent to `b`

## Template: Resumable iterator (the OpenAI archetype)

```python
class ResumableLineIterator:
    """Iterates lines across multiple files. Can pause and resume from a state dict."""

    def __init__(self, file_paths: list[str]):
        self.file_paths = file_paths
        self.file_idx = 0          # index into file_paths
        self.line_offset = 0       # byte offset within current file
        self._current_handle = None

    def get_state(self) -> dict:
        # Only primitives. NO file handle, NO iterator object.
        return {
            "file_paths": list(self.file_paths),
            "file_idx": self.file_idx,
            "line_offset": self.line_offset,
        }

    def set_state(self, state: dict) -> None:
        self.file_paths = list(state["file_paths"])
        self.file_idx = state["file_idx"]
        self.line_offset = state["line_offset"]
        self._close_handle()

    def __iter__(self):
        return self

    def __next__(self) -> str:
        while self.file_idx < len(self.file_paths):
            if self._current_handle is None:
                self._open_current()
            line = self._current_handle.readline()
            if line:
                self.line_offset = self._current_handle.tell()
                return line
            # End of file — advance
            self._close_handle()
            self.file_idx += 1
            self.line_offset = 0
        raise StopIteration

    def _open_current(self):
        self._current_handle = open(self.file_paths[self.file_idx], "rb")
        self._current_handle.seek(self.line_offset)

    def _close_handle(self):
        if self._current_handle:
            self._current_handle.close()
            self._current_handle = None
```

**Usage — pause mid-stream and resume in a fresh instance:**

```python
it = ResumableLineIterator(["a.txt", "b.txt"])
print(next(it))           # reads first line of a.txt
saved = it.get_state()    # snapshot: {file_paths, file_idx=0, line_offset=<n>}

it2 = ResumableLineIterator([])
it2.set_state(saved)      # fresh instance, no open file handle yet
print(next(it2))          # picks up exactly where it left off
```

## Template: Length-prefix binary encoding (Redis / OpenAI KV style)

```python
def encode(records: list[tuple[str, str]]) -> bytes:
    """Serialize as: <key_len><key><val_len><val>... using 4-byte big-endian lengths."""
    out = bytearray()
    for key, value in records:
        kb, vb = key.encode("utf-8"), value.encode("utf-8")
        out += len(kb).to_bytes(4, "big") + kb
        out += len(vb).to_bytes(4, "big") + vb
    return bytes(out)

def decode(data: bytes) -> list[tuple[str, str]]:
    out = []
    i = 0
    while i < len(data):
        klen = int.from_bytes(data[i:i+4], "big"); i += 4
        key = data[i:i+klen].decode("utf-8");      i += klen
        vlen = int.from_bytes(data[i:i+4], "big"); i += 4
        val = data[i:i+vlen].decode("utf-8");      i += vlen
        out.append((key, val))
    return out
```

*Why not JSON?* JSON cannot represent raw bytes, bloats numeric values as strings, and requires a delimiter scan. Length-prefix is O(1) per-field advance and survives embedded quotes, newlines, or null bytes in values.

## Template: BACKUP / RESTORE with TTL re-anchoring

```python
def backup(db: dict, current_ts: int) -> dict:
    """Snapshot non-expired entries with REMAINING TTL (not absolute expiry)."""
    snapshot = {}
    for key, fields in db.items():
        snapshot[key] = {}
        for field, (value, expiry_ts) in fields.items():
            if expiry_ts is None:
                snapshot[key][field] = (value, None)
            elif expiry_ts > current_ts:
                snapshot[key][field] = (value, expiry_ts - current_ts)  # remaining
            # else: expired, skip
    return snapshot

def restore(snapshot: dict, restore_ts: int) -> dict:
    """Re-anchor TTLs: new_expiry = restore_ts + remaining_ttl."""
    db = {}
    for key, fields in snapshot.items():
        db[key] = {}
        for field, (value, remaining) in fields.items():
            if remaining is None:
                db[key][field] = (value, None)
            else:
                db[key][field] = (value, restore_ts + remaining)
    return db
```

*Key insight:* storing `expiry_ts - current_ts` (remaining) rather than `expiry_ts` (absolute) means RESTORE at any later timestamp gives the correct lifespan. Storing the absolute timestamp would cause entries to expire immediately if restored after their original wall-clock expiry.

## Template: Snapshot a class to dict and back

```python
from dataclasses import dataclass, asdict

@dataclass
class CounterState:
    count: int
    step: int
    label: str

class ResumableCounter:
    def __init__(self, label: str, step: int = 1):
        self._state = CounterState(count=0, step=step, label=label)

    def increment(self):
        self._state.count += self._state.step

    def get_state(self) -> dict:
        return asdict(self._state)          # pure primitives

    def set_state(self, state: dict) -> None:
        self._state = CounterState(**state) # reconstruct from dict

    @property
    def value(self):
        return self._state.count

# Round-trip
c1 = ResumableCounter("hits", step=5)
c1.increment(); c1.increment()
snapshot = c1.get_state()                   # {"count": 10, "step": 5, "label": "hits"}

c2 = ResumableCounter("_")
c2.set_state(snapshot)
assert c2.value == c1.value                 # equivalent instances
```

## Variants / Gotchas

- **Never store live objects in state** — file handles, iterators, locks, threads, sockets all fail to serialize and can't survive a process restart; re-derive them inside `set_state` or lazily on first use
- **Pickle is a local-only shortcut** — not portable across Python versions, a security hole if state comes from untrusted sources, and slower than JSON for plain dicts; most interviews want JSON-compatible state
- **TTL: store remaining, not absolute** — `expiry_ts - current_ts` in backup; `restore_ts + remaining` on restore; storing the absolute timestamp silently breaks lifespan after any delay
- **`get_state` / `set_state` must round-trip** — `inst.set_state(other.get_state())` should produce an instance that behaves identically to `other`; test this explicitly with assertions
- **Length-prefix beats JSON for binary problems** — OpenAI's KV store problems explicitly want byte-level encoding; JSON cannot handle raw bytes and adds framing overhead
- **Atomicity on restore** — validate quota / capacity constraints before mutating any state; if the restored snapshot wouldn't fit (e.g. storage quota), return early without partial writes (see Problem 04)
- **Test pause/resume explicitly** — snapshot mid-stream, pass state to a fresh instance with `set_state`, verify it produces identical remaining output to the original

## Choosing your encoding

| Format | Pros | Cons | When |
|--------|------|------|------|
| `pickle` | works on anything | not portable, security hole, slow | quick local prototyping only |
| `json` | portable, human-readable | no bytes, no NaN, no datetimes | most interview problems |
| custom length-prefix | compact, exact bytes, O(1) field advance | manual parsing | OpenAI KV store, real binary interviews |
| `dataclasses.asdict` | clean for plain data classes | fails on non-trivial nested types | dataclass-based state objects |

## Practice

- **In-repo Problem 02 — In-Memory Database (L4 BACKUP/RESTORE)** — full 4-level KV store ending in BACKUP/RESTORE with TTL re-anchoring. *Insight:* store `remaining_ttl` in snapshot, not absolute expiry — restore re-anchors with `new_expiry = restore_ts + remaining`. [/Users/vyvyen/code/interview/02-in-memory-db](https://github.com/vyvy3n/interview/blob/main/02-in-memory-db/solution.py)
- **In-repo Problem 04 — Cloud Storage (L4 BACKUP)** — snapshot user files + share lists; restore validates quota first (atomic on overflow). *Insight:* atomicity check BEFORE any state mutation; if quota wouldn't fit, return without changing anything. [/Users/vyvyen/code/interview/04-cloud-storage](https://github.com/vyvy3n/interview/blob/main/04-cloud-storage/solution.py)
- **OpenAI Resumable Multi-File Iterator** — actual question from OpenAI's confirmed 8-problem bank. *Insight:* state = primitives only (`file_paths`, `file_idx`, `line_offset`); never store the file handle or iterator object — re-derive on resume. (See template above.)
- **OpenAI Versioned KV Store** — actual question from OpenAI's bank. *Insight:* length-prefix binary encoding for keys+values; supports concurrent reads while serializing writes on disk. (See encode/decode template above.)
