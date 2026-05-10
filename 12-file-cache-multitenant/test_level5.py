"""
Level 5 tests — Async concurrent access with asyncio.Lock
Run: python3 test_level5.py
"""

import unittest
import asyncio
from solution import FileCache


class TestLevel5AsyncBasicOps(unittest.IsolatedAsyncioTestCase):
    async def test_astore_new_file_returns_true(self):
        cache = FileCache()
        self.assertTrue(await cache.astore("f.txt", "data"))

    async def test_astore_duplicate_returns_false(self):
        cache = FileCache()
        await cache.astore("f.txt", "data")
        self.assertFalse(await cache.astore("f.txt", "other"))

    async def test_afetch_existing_returns_content(self):
        cache = FileCache()
        await cache.astore("f.txt", "hello")
        self.assertEqual(await cache.afetch("f.txt"), "hello")

    async def test_afetch_missing_returns_empty_string(self):
        cache = FileCache()
        self.assertEqual(await cache.afetch("missing.txt"), "")

    async def test_aremove_existing_returns_true(self):
        cache = FileCache()
        await cache.astore("f.txt", "data")
        self.assertTrue(await cache.aremove("f.txt"))

    async def test_aremove_missing_returns_false(self):
        cache = FileCache()
        self.assertFalse(await cache.aremove("ghost.txt"))

    async def test_aremove_deletes_file(self):
        cache = FileCache()
        await cache.astore("f.txt", "data")
        await cache.aremove("f.txt")
        self.assertEqual(await cache.afetch("f.txt"), "")

    async def test_aupdate_existing_returns_true(self):
        cache = FileCache()
        await cache.astore("f.txt", "old")
        self.assertTrue(await cache.aupdate("f.txt", "new"))

    async def test_aupdate_missing_returns_false(self):
        cache = FileCache()
        self.assertFalse(await cache.aupdate("ghost.txt", "data"))

    async def test_aupdate_changes_content(self):
        cache = FileCache()
        await cache.astore("f.txt", "old")
        await cache.aupdate("f.txt", "new")
        self.assertEqual(await cache.afetch("f.txt"), "new")

    async def test_astore_returns_bool(self):
        cache = FileCache()
        result = await cache.astore("f.txt", "x")
        self.assertIsInstance(result, bool)

    async def test_aremove_returns_bool(self):
        cache = FileCache()
        result = await cache.aremove("ghost.txt")
        self.assertIsInstance(result, bool)


class TestLevel5AsyncTenantOps(unittest.IsolatedAsyncioTestCase):
    async def test_atenant_store_new_returns_true(self):
        cache = FileCache()
        cache.register_tenant("t1", 10)
        self.assertTrue(await cache.atenant_store("t1", "f.txt", "data"))

    async def test_atenant_store_exceeds_quota_returns_false(self):
        cache = FileCache()
        cache.register_tenant("t1", 1)
        await cache.atenant_store("t1", "f1.txt", "A")
        self.assertFalse(await cache.atenant_store("t1", "f2.txt", "B"))

    async def test_atenant_fetch_returns_correct_content(self):
        cache = FileCache()
        cache.register_tenant("alice", 10)
        await cache.atenant_store("alice", "notes.txt", "alice's notes")
        self.assertEqual(await cache.atenant_fetch("alice", "notes.txt"), "alice's notes")

    async def test_atenant_fetch_missing_returns_empty(self):
        cache = FileCache()
        cache.register_tenant("t1", 10)
        self.assertEqual(await cache.atenant_fetch("t1", "ghost.txt"), "")

    async def test_atenant_isolation_async(self):
        cache = FileCache()
        cache.register_tenant("alice", 10)
        cache.register_tenant("bob", 10)
        await asyncio.gather(
            cache.atenant_store("alice", "f.txt", "alice-data"),
            cache.atenant_store("bob", "f.txt", "bob-data"),
        )
        alice_val = await cache.atenant_fetch("alice", "f.txt")
        bob_val = await cache.atenant_fetch("bob", "f.txt")
        self.assertEqual(alice_val, "alice-data")
        self.assertEqual(bob_val, "bob-data")


class TestLevel5ConcurrentStores(unittest.IsolatedAsyncioTestCase):
    async def test_50_concurrent_stores_different_files_no_data_loss(self):
        cache = FileCache()
        await asyncio.gather(*[cache.astore(f"f{i}.txt", f"v{i}") for i in range(50)])
        for i in range(50):
            val = await cache.afetch(f"f{i}.txt")
            self.assertEqual(val, f"v{i}", f"f{i}.txt had wrong value: {val!r}")

    async def test_100_concurrent_stores_all_land(self):
        cache = FileCache()
        await asyncio.gather(*[cache.astore(f"file{i:03d}.txt", str(i)) for i in range(100)])
        self.assertEqual(cache.size(), 100)

    async def test_concurrent_stores_same_file_only_first_wins(self):
        cache = FileCache()
        results = await asyncio.gather(*[cache.astore("shared.txt", str(i)) for i in range(50)])
        # Exactly one should succeed
        true_count = sum(1 for r in results if r is True)
        self.assertEqual(true_count, 1)
        self.assertEqual(cache.size(), 1)

    async def test_concurrent_removes_exactly_one_succeeds(self):
        cache = FileCache()
        await cache.astore("f.txt", "data")
        results = await asyncio.gather(*[cache.aremove("f.txt") for _ in range(20)])
        true_count = sum(1 for r in results if r is True)
        self.assertEqual(true_count, 1)
        self.assertEqual(await cache.afetch("f.txt"), "")


class TestLevel5MixedSyncAsync(unittest.IsolatedAsyncioTestCase):
    async def test_sync_store_then_async_fetch(self):
        cache = FileCache()
        cache.store("sync_file.txt", "sync_data")
        self.assertEqual(await cache.afetch("sync_file.txt"), "sync_data")

    async def test_async_store_then_sync_fetch(self):
        cache = FileCache()
        await cache.astore("async_file.txt", "async_data")
        self.assertEqual(cache.fetch("async_file.txt"), "async_data")

    async def test_sync_and_async_see_same_state(self):
        cache = FileCache()
        cache.store("f1.txt", "A")
        await cache.astore("f2.txt", "B")
        self.assertEqual(cache.size(), 2)
        self.assertEqual(await cache.afetch("f1.txt"), "A")
        self.assertEqual(cache.fetch("f2.txt"), "B")

    async def test_l2_methods_still_work_after_async_ops(self):
        cache = FileCache()
        await cache.astore("log_a.txt", "aaa")
        await cache.astore("log_b.txt", "bbb")
        await cache.astore("other.txt", "ccc")
        result = cache.fetch_by_prefix("log_")
        self.assertEqual(result, ["log_a.txt", "log_b.txt"])
        self.assertEqual(cache.get_total_size(), 9)

    async def test_l3_set_capacity_works_after_async_stores(self):
        cache = FileCache()
        await asyncio.gather(*[cache.astore(f"f{i}.txt", "data") for i in range(10)])
        evicted = cache.set_capacity(5)
        self.assertEqual(evicted, 5)
        self.assertEqual(cache.size(), 5)


class TestLevel5ConcurrentTenants(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_tenant_stores_no_corruption(self):
        cache = FileCache()
        cache.register_tenant("t1", 50)
        cache.register_tenant("t2", 50)
        t1_tasks = [cache.atenant_store("t1", f"t1f{i}.txt", f"v{i}") for i in range(30)]
        t2_tasks = [cache.atenant_store("t2", f"t2f{i}.txt", f"v{i}") for i in range(30)]
        await asyncio.gather(*(t1_tasks + t2_tasks))
        # Each tenant should have 30 files
        self.assertEqual(cache.tenant_size("t1"), 30)
        self.assertEqual(cache.tenant_size("t2"), 30)

    async def test_concurrent_stores_respect_quota(self):
        cache = FileCache()
        cache.register_tenant("limited", 5)
        results = await asyncio.gather(
            *[cache.atenant_store("limited", f"f{i}.txt", "data") for i in range(20)]
        )
        true_count = sum(1 for r in results if r is True)
        self.assertEqual(true_count, 5)
        self.assertEqual(cache.tenant_size("limited"), 5)

    async def test_large_concurrent_gather_no_crash(self):
        cache = FileCache()
        tasks = [cache.astore(f"k{i % 50}.txt", str(i)) for i in range(200)]
        await asyncio.gather(*tasks)
        # Every key should have some valid value
        for i in range(50):
            val = await cache.afetch(f"k{i}.txt")
            # Must be a string; either empty (if evicted) or a numeric string
            self.assertIsInstance(val, str)


if __name__ == "__main__":
    unittest.main()
