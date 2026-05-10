"""
Problem 12: Multi-Tenant File Cache
====================================

Implement the FileCache class below. Work level by level:
  - Level 1: store / fetch / remove / size  (single-tenant, no constraints)
  - Level 2: update / fetch_by_prefix / get_total_size
  - Level 3: set_capacity (LRU eviction with monotonic access counter)
  - Level 4: register_tenant / tenant_* ops (per-tenant quota, shared LRU)
  - Level 5: async methods astore / afetch / aremove / aupdate / atenant_store / atenant_fetch
  - Level 6: acompare_and_update / astore_or_update / abulk_store  (atomic compound ops)

Run tests:
  python3 test_level1.py    # ... through test_level6.py
"""

import asyncio
from collections import OrderedDict


_GLOBAL_TENANT = "__global__"


class FileCache:
    def __init__(self):
        # _files: maps (tenant_id, filename) -> content (str)
        self._files: dict = {}

        # LRU tracking: maps (tenant_id, filename) -> tick (int)
        # lower tick = accessed longer ago = evict first
        self._lru: dict = {}
        self._tick: int = 0

        # Cache-wide capacity (max total files across all tenants). None = unbounded.
        self._capacity: int | None = None

        # Tenant registry: maps tenant_id -> file_quota (int | None)
        # None quota means no per-tenant limit.
        # The global tenant is always present with no quota.
        self._tenants: dict = {_GLOBAL_TENANT: None}

        # Per-tenant file counts (derived, but kept in sync for O(1) quota checks)
        self._tenant_counts: dict = {_GLOBAL_TENANT: 0}

        # asyncio lock for L5-L6; created lazily to survive pickling / no-event-loop envs
        self._lock: asyncio.Lock | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_lock(self) -> asyncio.Lock:
        """Return the asyncio lock, creating it if needed."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def _touch(self, tenant_id: str, filename: str) -> None:
        """Update LRU counter for a (tenant, file) pair."""
        key = (tenant_id, filename)
        self._lru[key] = self._tick
        self._tick += 1

    def _evict_one(self) -> None:
        """Evict the globally LRU file (lowest tick)."""
        if not self._lru:
            return
        lru_key = min(self._lru, key=lambda k: self._lru[k])
        tenant_id, filename = lru_key
        del self._files[lru_key]
        del self._lru[lru_key]
        self._tenant_counts[tenant_id] -= 1

    def _maybe_evict_for_new_file(self) -> None:
        """If at global capacity, evict LRU to make room for one new file."""
        if self._capacity is not None and len(self._files) >= self._capacity:
            self._evict_one()

    def _total_file_count(self) -> int:
        return len(self._files)

    # ------------------------------------------------------------------
    # LEVEL 1 — Basic file ops (single-tenant)
    # ------------------------------------------------------------------

    def store(self, filename: str, content: str) -> bool:
        """
        Store file under filename with content.
        Returns True if newly stored, False if filename already existed (no overwrite).
        """
        return self._do_store(_GLOBAL_TENANT, filename, content)

    def fetch(self, filename: str) -> str:
        """Return content of filename, or '' if missing. Updates LRU on hit."""
        return self._do_fetch(_GLOBAL_TENANT, filename)

    def remove(self, filename: str) -> bool:
        """Remove filename. Returns True if removed, False if missing."""
        return self._do_remove(_GLOBAL_TENANT, filename)

    def size(self) -> int:
        """Return count of files in the global tenant."""
        return self._tenant_counts[_GLOBAL_TENANT]

    # ------------------------------------------------------------------
    # LEVEL 2 — Updates + queries
    # ------------------------------------------------------------------

    def update(self, filename: str, content: str) -> bool:
        """
        Overwrite content of filename.
        Returns True if updated, False if filename missing (does NOT create).
        """
        return self._do_update(_GLOBAL_TENANT, filename, content)

    def fetch_by_prefix(self, prefix: str) -> list:
        """
        Return sorted list of filenames (global tenant) whose names start with prefix.
        Does NOT update LRU (metadata query).
        """
        return self._tenant_fetch_by_prefix(_GLOBAL_TENANT, prefix)

    def get_total_size(self) -> int:
        """Return sum of len(content) over all files in the global tenant."""
        return sum(
            len(content)
            for (tid, _), content in self._files.items()
            if tid == _GLOBAL_TENANT
        )

    # ------------------------------------------------------------------
    # LEVEL 3 — Capacity + LRU eviction
    # ------------------------------------------------------------------

    def set_capacity(self, max_files: int) -> int:
        """
        Set global max file count (across all tenants).
        Immediately evict LRU until count <= max_files.
        Returns count evicted.
        """
        self._capacity = max_files
        evicted = 0
        while self._total_file_count() > max_files:
            self._evict_one()
            evicted += 1
        return evicted

    # ------------------------------------------------------------------
    # LEVEL 4 — Multi-tenant
    # ------------------------------------------------------------------

    def register_tenant(self, tenant_id: str, file_quota: int) -> bool:
        """
        Register a new tenant with a per-tenant file quota.
        Returns False if tenant_id already registered.
        """
        if tenant_id in self._tenants:
            return False
        self._tenants[tenant_id] = file_quota
        self._tenant_counts[tenant_id] = 0
        return True

    def _tenant_fetch_by_prefix(self, tenant_id: str, prefix: str) -> list:
        """Return sorted filenames for tenant starting with prefix. Does NOT update LRU."""
        if tenant_id not in self._tenants:
            return []
        return sorted(
            fname
            for (tid, fname) in self._files
            if tid == tenant_id and fname.startswith(prefix)
        )

    # Public tenant-prefixed API
    def tenant_store(self, tenant_id: str, filename: str, content: str) -> bool:
        return self._do_store(tenant_id, filename, content)

    def tenant_fetch(self, tenant_id: str, filename: str) -> str:
        return self._do_fetch(tenant_id, filename)

    def tenant_remove(self, tenant_id: str, filename: str) -> bool:
        return self._do_remove(tenant_id, filename)

    def tenant_update(self, tenant_id: str, filename: str, content: str) -> bool:
        return self._do_update(tenant_id, filename, content)

    def tenant_fetch_by_prefix(self, tenant_id: str, prefix: str) -> list:
        return self._tenant_fetch_by_prefix(tenant_id, prefix)

    def tenant_size(self, tenant_id: str) -> int:
        if tenant_id not in self._tenants:
            return 0
        return self._tenant_counts[tenant_id]

    # ------------------------------------------------------------------
    # LEVEL 5 — Async concurrent access (asyncio)
    # ------------------------------------------------------------------

    async def astore(self, filename: str, content: str) -> bool:
        """Async store (global tenant). Acquires lock."""
        async with self._get_lock():
            return self._do_store(_GLOBAL_TENANT, filename, content)

    async def afetch(self, filename: str) -> str:
        """Async fetch (global tenant). Acquires lock."""
        async with self._get_lock():
            return self._do_fetch(_GLOBAL_TENANT, filename)

    async def aremove(self, filename: str) -> bool:
        """Async remove (global tenant). Acquires lock."""
        async with self._get_lock():
            return self._do_remove(_GLOBAL_TENANT, filename)

    async def aupdate(self, filename: str, content: str) -> bool:
        """Async update (global tenant). Acquires lock."""
        async with self._get_lock():
            return self._do_update(_GLOBAL_TENANT, filename, content)

    async def atenant_store(self, tenant_id: str, filename: str, content: str) -> bool:
        """Async tenant store. Acquires lock."""
        async with self._get_lock():
            return self._do_store(tenant_id, filename, content)

    async def atenant_fetch(self, tenant_id: str, filename: str) -> str:
        """Async tenant fetch. Acquires lock."""
        async with self._get_lock():
            return self._do_fetch(tenant_id, filename)

    async def atenant_remove(self, tenant_id: str, filename: str) -> bool:
        """Async tenant remove. Acquires lock."""
        async with self._get_lock():
            return self._do_remove(tenant_id, filename)

    async def atenant_update(self, tenant_id: str, filename: str, content: str) -> bool:
        """Async tenant update. Acquires lock."""
        async with self._get_lock():
            return self._do_update(tenant_id, filename, content)

    # Internal locked helpers (called while lock is already held by async methods,
    # or directly by sync methods which don't need the lock).

    def _do_store(self, tenant_id: str, filename: str, content: str) -> bool:
        if tenant_id not in self._tenants:
            return False
        key = (tenant_id, filename)
        if key in self._files:
            return False
        quota = self._tenants[tenant_id]
        if quota is not None and self._tenant_counts[tenant_id] >= quota:
            return False
        self._maybe_evict_for_new_file()
        self._files[key] = content
        self._tenant_counts[tenant_id] += 1
        self._touch(tenant_id, filename)
        return True

    def _do_fetch(self, tenant_id: str, filename: str) -> str:
        if tenant_id not in self._tenants:
            return ""
        key = (tenant_id, filename)
        if key not in self._files:
            return ""
        self._touch(tenant_id, filename)
        return self._files[key]

    def _do_remove(self, tenant_id: str, filename: str) -> bool:
        if tenant_id not in self._tenants:
            return False
        key = (tenant_id, filename)
        if key not in self._files:
            return False
        del self._files[key]
        self._lru.pop(key, None)
        self._tenant_counts[tenant_id] -= 1
        return True

    def _do_update(self, tenant_id: str, filename: str, content: str) -> bool:
        if tenant_id not in self._tenants:
            return False
        key = (tenant_id, filename)
        if key not in self._files:
            return False
        self._files[key] = content
        self._touch(tenant_id, filename)
        return True

    # ------------------------------------------------------------------
    # LEVEL 6 — Atomic compound operations
    # ------------------------------------------------------------------

    async def acompare_and_update(
        self, filename: str, expected_content: str, new_content: str
    ) -> bool:
        """
        Atomically: if current content of filename == expected_content,
        update to new_content and return True. Else return False.
        Returns False if file is missing.
        """
        async with self._get_lock():
            key = (_GLOBAL_TENANT, filename)
            if key not in self._files:
                return False
            if self._files[key] != expected_content:
                return False
            self._files[key] = new_content
            self._touch(_GLOBAL_TENANT, filename)
            return True

    async def astore_or_update(self, filename: str, content: str) -> str:
        """
        Atomically: if file exists, update and return 'updated'.
        If file does not exist, store and return 'stored'.
        """
        async with self._get_lock():
            key = (_GLOBAL_TENANT, filename)
            if key in self._files:
                self._files[key] = content
                self._touch(_GLOBAL_TENANT, filename)
                return "updated"
            else:
                self._maybe_evict_for_new_file()
                self._files[key] = content
                self._tenant_counts[_GLOBAL_TENANT] += 1
                self._touch(_GLOBAL_TENANT, filename)
                return "stored"

    async def abulk_store(self, items: list) -> int:
        """
        Atomically store multiple (filename, content) pairs (global tenant).
        All-or-nothing: if ANY filename in items already exists, NONE are stored.
        Returns count stored (0 if any duplicate detected).
        """
        async with self._get_lock():
            # Check for duplicates within items list itself
            filenames = [fname for fname, _ in items]
            if len(filenames) != len(set(filenames)):
                return 0
            # Check for any existing file collisions
            for filename in filenames:
                key = (_GLOBAL_TENANT, filename)
                if key in self._files:
                    return 0
            # Check capacity: if we'd overflow, evict enough (or fail if no room)
            # Evict LRU to make room for all new files
            new_count = len(items)
            if self._capacity is not None:
                while self._total_file_count() + new_count > self._capacity:
                    if not self._lru:
                        return 0
                    self._evict_one()
            # All good — store all
            for filename, content in items:
                key = (_GLOBAL_TENANT, filename)
                self._files[key] = content
                self._tenant_counts[_GLOBAL_TENANT] += 1
                self._touch(_GLOBAL_TENANT, filename)
            return new_count
