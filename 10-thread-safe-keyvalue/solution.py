"""
Problem 10: Async In-Memory Key-Value Store
===========================================

Implement the KVStore class below. Work level by level:
  - Level 1: put / get / delete
  - Level 2: multi_get / keys_by_prefix / count
  - Level 3: put_with_ttl / get_at / cleanup_expired
  - Level 4: set_capacity (LRU eviction)
  - Level 5: aget / aput / adelete  (asyncio)
  - Level 6: acompare_and_set / aget_and_set / aincrement  (asyncio atomic)

Run tests:
  python3 test_level1.py    # ... through test_level6.py
"""

import asyncio


class KVStore:
    def __init__(self):
        # _store maps key -> value (str)
        self._store: dict = {}
        # _expiry maps key -> expiry timestamp (int), only for TTL'd keys
        self._expiry: dict = {}
        # LRU: _last_access maps key -> tick (int); monotonic counter
        self._tick: int = 0
        self._last_access: dict = {}
        # Capacity limit; None means unbounded
        self._capacity: int | None = None
        # asyncio lock for L5-L6
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _touch(self, key: str) -> None:
        """Record an access for LRU tracking (only on hits/writes)."""
        self._last_access[key] = self._tick
        self._tick += 1

    def _evict_lru_one(self) -> None:
        """Evict the single LRU entry (lowest tick)."""
        lru_key = min(self._last_access, key=lambda k: self._last_access[k])
        del self._store[lru_key]
        del self._last_access[lru_key]
        self._expiry.pop(lru_key, None)

    def _maybe_evict_for_new_key(self) -> None:
        """If at capacity, evict LRU to make room for one new key."""
        if self._capacity is not None and len(self._store) >= self._capacity:
            self._evict_lru_one()

    # ------------------------------------------------------------------
    # LEVEL 1 — Basic put / get / delete
    # ------------------------------------------------------------------

    def put(self, key: str, value: str) -> None:
        """Store value under key. Overwrites if exists. Clears any TTL."""
        is_new = key not in self._store
        if is_new:
            self._maybe_evict_for_new_key()
        self._store[key] = value
        # Clear any existing TTL
        self._expiry.pop(key, None)
        self._touch(key)

    def get(self, key: str) -> str:
        """Return value for key, or '' if missing. Does NOT check TTL."""
        if key not in self._store:
            return ""
        self._touch(key)
        return self._store[key]

    def delete(self, key: str) -> bool:
        """Remove key. Returns True if it existed, False otherwise."""
        if key not in self._store:
            return False
        del self._store[key]
        self._expiry.pop(key, None)
        self._last_access.pop(key, None)
        return True

    # ------------------------------------------------------------------
    # LEVEL 2 — Bulk operations and prefix queries
    # ------------------------------------------------------------------

    def multi_get(self, keys: list) -> list:
        """Return list of values for keys, '' for missing, same order as input."""
        return [self.get(k) for k in keys]

    def keys_by_prefix(self, prefix: str) -> list:
        """Return all keys starting with prefix, sorted alphabetically."""
        return sorted(k for k in self._store if k.startswith(prefix))

    def count(self) -> int:
        """Return number of keys currently in store."""
        return len(self._store)

    # ------------------------------------------------------------------
    # LEVEL 3 — TTL / expiration
    # ------------------------------------------------------------------

    def put_with_ttl(self, key: str, value: str, ttl: int, now: int) -> None:
        """Store value with expiry at now+ttl. Overwrites existing entry."""
        is_new = key not in self._store
        if is_new:
            self._maybe_evict_for_new_key()
        self._store[key] = value
        self._expiry[key] = now + ttl
        self._touch(key)

    def get_at(self, key: str, now: int) -> str:
        """Return value if not expired at 'now', else ''. Updates LRU stamp on hit."""
        if key not in self._store:
            return ""
        expiry = self._expiry.get(key)
        if expiry is not None and expiry <= now:
            # Expired — treat as miss (do NOT update LRU)
            return ""
        # Hit: update LRU
        self._touch(key)
        return self._store[key]

    def cleanup_expired(self, now: int) -> int:
        """Remove entries with expiry <= now. Returns count removed."""
        to_remove = [
            k for k, exp in self._expiry.items() if exp <= now
        ]
        for k in to_remove:
            del self._store[k]
            del self._expiry[k]
            self._last_access.pop(k, None)
        return len(to_remove)

    # ------------------------------------------------------------------
    # LEVEL 4 — Capacity cap and LRU eviction
    # ------------------------------------------------------------------

    def set_capacity(self, max_keys: int) -> int:
        """
        Set max entry count. Immediately evict LRU entries if over limit.
        Returns count evicted. No capacity limit until this is called.
        """
        self._capacity = max_keys
        evicted = 0
        while len(self._store) > max_keys:
            self._evict_lru_one()
            evicted += 1
        return evicted

    # ------------------------------------------------------------------
    # LEVEL 5 — Async concurrent access
    # ------------------------------------------------------------------

    async def aget(self, key: str) -> str:
        """Async get. Acquires lock before reading."""
        async with self._lock:
            if key not in self._store:
                return ""
            self._touch(key)
            return self._store[key]

    async def aput(self, key: str, value: str) -> None:
        """Async put. Acquires lock before writing."""
        async with self._lock:
            is_new = key not in self._store
            if is_new:
                self._maybe_evict_for_new_key()
            self._store[key] = value
            self._expiry.pop(key, None)
            self._touch(key)

    async def adelete(self, key: str) -> bool:
        """Async delete. Acquires lock. Returns True if deleted, False if missing."""
        async with self._lock:
            if key not in self._store:
                return False
            del self._store[key]
            self._expiry.pop(key, None)
            self._last_access.pop(key, None)
            return True

    # ------------------------------------------------------------------
    # LEVEL 6 — Atomic compound operations
    # ------------------------------------------------------------------

    async def acompare_and_set(self, key: str, expected: str, new_value: str) -> bool:
        """
        Atomically: if current value == expected, set to new_value and return True.
        Returns False if current value != expected.
        Special: if key is missing and expected == '', insert new_value and return True.
        """
        async with self._lock:
            current = self._store.get(key)  # None if missing
            if current is None:
                # Key is missing; treat as "" for comparison
                if expected == "":
                    # Insert-if-absent
                    is_new = True
                    if is_new:
                        self._maybe_evict_for_new_key()
                    self._store[key] = new_value
                    self._expiry.pop(key, None)
                    self._touch(key)
                    return True
                else:
                    return False
            else:
                if current == expected:
                    self._store[key] = new_value
                    self._expiry.pop(key, None)
                    self._touch(key)
                    return True
                else:
                    return False

    async def aget_and_set(self, key: str, new_value: str) -> str:
        """
        Atomically: read current value (or ''), set to new_value. Return OLD value.
        Always writes new_value even if key was missing.
        """
        async with self._lock:
            old = self._store.get(key, "")
            is_new = key not in self._store
            if is_new:
                self._maybe_evict_for_new_key()
            self._store[key] = new_value
            self._expiry.pop(key, None)
            self._touch(key)
            return old

    async def aincrement(self, key: str, delta: int) -> int:
        """
        Atomically: parse current value as int (0 if missing/invalid),
        add delta, store as string. Return new int value.
        """
        async with self._lock:
            raw = self._store.get(key, "0")
            try:
                current = int(raw)
            except ValueError:
                current = 0
            new_val = current + delta
            is_new = key not in self._store
            if is_new:
                self._maybe_evict_for_new_key()
            self._store[key] = str(new_val)
            self._expiry.pop(key, None)
            self._touch(key)
            return new_val
