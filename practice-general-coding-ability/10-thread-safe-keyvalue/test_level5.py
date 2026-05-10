"""
Level 5 tests — Async concurrent access with asyncio.Lock
Run: python3 test_level5.py
"""

import unittest
import asyncio
from solution import KVStore


class TestLevel5AsyncBasicOps(unittest.IsolatedAsyncioTestCase):
    async def test_aput_then_aget(self):
        kv = KVStore()
        await kv.aput("key", "value")
        self.assertEqual(await kv.aget("key"), "value")

    async def test_aget_missing_returns_empty_string(self):
        kv = KVStore()
        self.assertEqual(await kv.aget("nonexistent"), "")

    async def test_aput_overwrites(self):
        kv = KVStore()
        await kv.aput("k", "first")
        await kv.aput("k", "second")
        self.assertEqual(await kv.aget("k"), "second")

    async def test_adelete_existing_returns_true(self):
        kv = KVStore()
        await kv.aput("k", "v")
        self.assertTrue(await kv.adelete("k"))

    async def test_adelete_missing_returns_false(self):
        kv = KVStore()
        self.assertFalse(await kv.adelete("nope"))

    async def test_adelete_removes_key(self):
        kv = KVStore()
        await kv.aput("k", "v")
        await kv.adelete("k")
        self.assertEqual(await kv.aget("k"), "")

    async def test_adelete_returns_bool(self):
        kv = KVStore()
        await kv.aput("k", "v")
        result = await kv.adelete("k")
        self.assertIsInstance(result, bool)

    async def test_aput_returns_none(self):
        kv = KVStore()
        result = await kv.aput("k", "v")
        self.assertIsNone(result)


class TestLevel5ConcurrentPuts(unittest.IsolatedAsyncioTestCase):
    async def test_100_concurrent_puts_different_keys(self):
        """All 100 puts to different keys must land without corruption."""
        kv = KVStore()
        await asyncio.gather(*[kv.aput(f"k{i}", str(i)) for i in range(100)])
        for i in range(100):
            val = await kv.aget(f"k{i}")
            self.assertEqual(val, str(i), f"Key k{i} had wrong value: {val!r}")

    async def test_concurrent_put_then_get_same_key(self):
        """Many writers on same key — final value must be one of the written values."""
        kv = KVStore()
        await asyncio.gather(*[kv.aput("shared", str(i)) for i in range(50)])
        val = await kv.aget("shared")
        # val must be a string representation of some integer 0..49
        self.assertIn(val, [str(i) for i in range(50)])

    async def test_concurrent_put_and_delete(self):
        """After concurrent puts and deletes, store must be consistent."""
        kv = KVStore()
        # put 50 keys
        await asyncio.gather(*[kv.aput(f"k{i}", str(i)) for i in range(50)])
        # concurrently delete them
        results = await asyncio.gather(*[kv.adelete(f"k{i}") for i in range(50)])
        # each delete either succeeded (True) or key was already gone (False)
        for r in results:
            self.assertIsInstance(r, bool)
        # after all deletes, nothing should remain
        for i in range(50):
            self.assertEqual(await kv.aget(f"k{i}"), "")

    async def test_200_concurrent_puts_count(self):
        """count() after 200 concurrent puts should equal 200."""
        kv = KVStore()
        await asyncio.gather(*[kv.aput(f"key{i}", "v") for i in range(200)])
        self.assertEqual(kv.count(), 200)


class TestLevel5MixedSyncAsync(unittest.IsolatedAsyncioTestCase):
    async def test_sync_and_async_see_same_state(self):
        """sync put then async get — same store."""
        kv = KVStore()
        kv.put("sync_key", "sync_val")
        self.assertEqual(await kv.aget("sync_key"), "sync_val")

    async def test_async_put_then_sync_get(self):
        kv = KVStore()
        await kv.aput("k", "v")
        self.assertEqual(kv.get("k"), "v")

    async def test_sync_l2_still_works(self):
        kv = KVStore()
        await kv.aput("user:alice", "1")
        await kv.aput("user:bob", "2")
        result = kv.keys_by_prefix("user:")
        self.assertEqual(result, ["user:alice", "user:bob"])

    async def test_async_delete_then_sync_get(self):
        kv = KVStore()
        kv.put("k", "v")
        await kv.adelete("k")
        self.assertEqual(kv.get("k"), "")


class TestLevel5ConcurrentReadsWrites(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_reads_and_writes_no_crash(self):
        """Mix of reads and writes concurrently — must not crash or corrupt."""
        kv = KVStore()
        await kv.aput("shared", "0")

        async def writer(i):
            await kv.aput(f"w{i}", str(i))

        async def reader(i):
            val = await kv.aget("shared")
            self.assertIn(val, ["0"])  # only one value was ever written

        ops = [writer(i) for i in range(50)] + [reader(i) for i in range(50)]
        await asyncio.gather(*ops)

    async def test_large_concurrent_gather(self):
        """500 concurrent puts across 100 distinct keys (5 writers per key)."""
        kv = KVStore()
        tasks = [kv.aput(f"k{i % 100}", str(i)) for i in range(500)]
        await asyncio.gather(*tasks)
        # Every key should have some value, no corruption
        for i in range(100):
            val = await kv.aget(f"k{i}")
            # Value must be a string representing an integer
            self.assertTrue(val.isdigit() or val == "", f"Corrupt value for k{i}: {val!r}")


if __name__ == "__main__":
    unittest.main()
