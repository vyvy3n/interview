"""
Level 6 tests — Atomic compound operations
Run: python3 test_level6.py
"""

import unittest
import asyncio
from solution import KVStore


class TestLevel6CompareAndSet(unittest.IsolatedAsyncioTestCase):
    async def test_cas_hit_correct_expected(self):
        kv = KVStore()
        await kv.aput("k", "old")
        result = await kv.acompare_and_set("k", "old", "new")
        self.assertTrue(result)
        self.assertEqual(await kv.aget("k"), "new")

    async def test_cas_wrong_expected_returns_false(self):
        kv = KVStore()
        await kv.aput("k", "actual")
        result = await kv.acompare_and_set("k", "wrong", "new")
        self.assertFalse(result)
        self.assertEqual(await kv.aget("k"), "actual")

    async def test_cas_missing_key_nonempty_expected_returns_false(self):
        kv = KVStore()
        result = await kv.acompare_and_set("missing", "anything", "new")
        self.assertFalse(result)
        self.assertEqual(await kv.aget("missing"), "")

    async def test_cas_insert_if_absent_empty_expected(self):
        """If key missing and expected == '', insert and return True."""
        kv = KVStore()
        result = await kv.acompare_and_set("new_key", "", "created")
        self.assertTrue(result)
        self.assertEqual(await kv.aget("new_key"), "created")

    async def test_cas_existing_key_empty_expected_returns_false(self):
        """If key exists, expected='' should return False (value != '')."""
        kv = KVStore()
        await kv.aput("k", "something")
        result = await kv.acompare_and_set("k", "", "new")
        self.assertFalse(result)
        self.assertEqual(await kv.aget("k"), "something")

    async def test_cas_returns_bool(self):
        kv = KVStore()
        result = await kv.acompare_and_set("k", "", "v")
        self.assertIsInstance(result, bool)

    async def test_cas_chained_updates(self):
        """Sequential CAS — each step only succeeds if previous committed."""
        kv = KVStore()
        await kv.acompare_and_set("k", "", "v1")   # insert
        r2 = await kv.acompare_and_set("k", "v1", "v2")
        self.assertTrue(r2)
        r3 = await kv.acompare_and_set("k", "v1", "v3")  # stale expected
        self.assertFalse(r3)
        self.assertEqual(await kv.aget("k"), "v2")


class TestLevel6GetAndSet(unittest.IsolatedAsyncioTestCase):
    async def test_get_and_set_existing_returns_old(self):
        kv = KVStore()
        await kv.aput("k", "old")
        old = await kv.aget_and_set("k", "new")
        self.assertEqual(old, "old")
        self.assertEqual(await kv.aget("k"), "new")

    async def test_get_and_set_missing_returns_empty_string(self):
        kv = KVStore()
        old = await kv.aget_and_set("k", "first")
        self.assertEqual(old, "")
        self.assertEqual(await kv.aget("k"), "first")

    async def test_get_and_set_always_writes(self):
        kv = KVStore()
        await kv.aget_and_set("k", "val")
        self.assertEqual(await kv.aget("k"), "val")

    async def test_get_and_set_swap_sequence(self):
        kv = KVStore()
        await kv.aput("token", "A")
        old1 = await kv.aget_and_set("token", "B")
        old2 = await kv.aget_and_set("token", "C")
        self.assertEqual(old1, "A")
        self.assertEqual(old2, "B")
        self.assertEqual(await kv.aget("token"), "C")

    async def test_get_and_set_returns_string(self):
        kv = KVStore()
        result = await kv.aget_and_set("k", "v")
        self.assertIsInstance(result, str)


class TestLevel6Increment(unittest.IsolatedAsyncioTestCase):
    async def test_increment_from_zero(self):
        kv = KVStore()
        await kv.aput("c", "0")
        result = await kv.aincrement("c", 1)
        self.assertEqual(result, 1)
        self.assertEqual(await kv.aget("c"), "1")

    async def test_increment_missing_key_treats_as_zero(self):
        kv = KVStore()
        result = await kv.aincrement("c", 5)
        self.assertEqual(result, 5)
        self.assertEqual(await kv.aget("c"), "5")

    async def test_increment_negative_delta(self):
        kv = KVStore()
        await kv.aput("c", "10")
        result = await kv.aincrement("c", -3)
        self.assertEqual(result, 7)

    async def test_increment_by_zero(self):
        kv = KVStore()
        await kv.aput("c", "42")
        result = await kv.aincrement("c", 0)
        self.assertEqual(result, 42)

    async def test_increment_invalid_value_treats_as_zero(self):
        kv = KVStore()
        await kv.aput("c", "not_a_number")
        result = await kv.aincrement("c", 1)
        self.assertEqual(result, 1)

    async def test_increment_returns_int(self):
        kv = KVStore()
        result = await kv.aincrement("c", 1)
        self.assertIsInstance(result, int)

    async def test_increment_stores_result_as_string(self):
        kv = KVStore()
        await kv.aincrement("c", 7)
        raw = await kv.aget("c")
        self.assertEqual(raw, "7")  # stored as string


class TestLevel6AtomicityUnderConcurrency(unittest.IsolatedAsyncioTestCase):
    async def test_100_concurrent_increments_no_lost_updates(self):
        """
        THE key atomicity test.
        Without proper locking, coroutines can interleave their read-compute-write
        and some updates are lost. With asyncio.Lock held for the full compound
        operation, the result must be exactly 100.
        """
        kv = KVStore()
        await kv.aput("counter", "0")
        await asyncio.gather(*[kv.aincrement("counter", 1) for _ in range(100)])
        final = await kv.aget("counter")
        self.assertEqual(final, "100",
                         f"Expected '100' but got '{final}' — likely a lost-update race condition")

    async def test_200_concurrent_increments_by_varying_delta(self):
        kv = KVStore()
        # 200 increments: 100 of delta=1 and 100 of delta=2; total = 300
        tasks = ([kv.aincrement("c", 1) for _ in range(100)] +
                 [kv.aincrement("c", 2) for _ in range(100)])
        await asyncio.gather(*tasks)
        self.assertEqual(await kv.aget("c"), "300")

    async def test_concurrent_cas_only_one_succeeds_per_value(self):
        """
        100 coroutines all try to CAS "" -> "claimed".
        Exactly one must succeed (insert-if-absent race).
        """
        kv = KVStore()
        results = await asyncio.gather(
            *[kv.acompare_and_set("lock", "", "claimed") for _ in range(100)]
        )
        true_count = sum(1 for r in results if r is True)
        self.assertEqual(true_count, 1,
                         f"Expected exactly 1 CAS success but got {true_count}")
        self.assertEqual(await kv.aget("lock"), "claimed")

    async def test_concurrent_get_and_set_no_corruption(self):
        """
        Many coroutines swapping the same key concurrently.
        The final value must be one of the written values.
        """
        kv = KVStore()
        await kv.aput("shared", "init")
        values = [f"v{i}" for i in range(50)]
        await asyncio.gather(*[kv.aget_and_set("shared", v) for v in values])
        final = await kv.aget("shared")
        # Final value must be one of the values we wrote
        self.assertIn(final, values,
                      f"Final value {final!r} is not one of the written values")

    async def test_mixed_atomic_operations_concurrently(self):
        """Mix all three atomic ops concurrently — no crash, no corruption."""
        kv = KVStore()
        await kv.aput("num", "0")
        await kv.aput("flag", "off")

        async def do_increment():
            await kv.aincrement("num", 1)

        async def do_cas():
            await kv.acompare_and_set("flag", "off", "on")

        async def do_swap():
            await kv.aget_and_set("flag", "off")

        tasks = (
            [do_increment() for _ in range(50)] +
            [do_cas() for _ in range(25)] +
            [do_swap() for _ in range(25)]
        )
        await asyncio.gather(*tasks)

        # num must be exactly 50
        self.assertEqual(await kv.aget("num"), "50")
        # flag must be a valid value (either "on" or "off")
        flag = await kv.aget("flag")
        self.assertIn(flag, ["on", "off"])


if __name__ == "__main__":
    unittest.main()
