"""
Level 6 tests — Atomic compound operations
Run: python3 test_level6.py

These tests are specifically designed to fail without proper async locking.
"""

import unittest
import asyncio
from solution import FileCache


class TestLevel6CompareAndUpdate(unittest.IsolatedAsyncioTestCase):
    async def test_compare_and_update_matching_content_returns_true(self):
        cache = FileCache()
        await cache.astore("f.txt", "version-1")
        result = await cache.acompare_and_update("f.txt", "version-1", "version-2")
        self.assertTrue(result)

    async def test_compare_and_update_updates_content(self):
        cache = FileCache()
        await cache.astore("f.txt", "v1")
        await cache.acompare_and_update("f.txt", "v1", "v2")
        self.assertEqual(await cache.afetch("f.txt"), "v2")

    async def test_compare_and_update_wrong_expected_returns_false(self):
        cache = FileCache()
        await cache.astore("f.txt", "actual")
        result = await cache.acompare_and_update("f.txt", "wrong", "new")
        self.assertFalse(result)

    async def test_compare_and_update_wrong_expected_leaves_content_unchanged(self):
        cache = FileCache()
        await cache.astore("f.txt", "actual")
        await cache.acompare_and_update("f.txt", "wrong", "new")
        self.assertEqual(await cache.afetch("f.txt"), "actual")

    async def test_compare_and_update_missing_file_returns_false(self):
        cache = FileCache()
        result = await cache.acompare_and_update("ghost.txt", "any", "new")
        self.assertFalse(result)

    async def test_compare_and_update_returns_bool(self):
        cache = FileCache()
        await cache.astore("f.txt", "v")
        result = await cache.acompare_and_update("f.txt", "v", "v2")
        self.assertIsInstance(result, bool)

    async def test_compare_and_update_chained(self):
        """Sequential CAS transitions: v1->v2->v3."""
        cache = FileCache()
        await cache.astore("f.txt", "v1")
        self.assertTrue(await cache.acompare_and_update("f.txt", "v1", "v2"))
        self.assertTrue(await cache.acompare_and_update("f.txt", "v2", "v3"))
        self.assertEqual(await cache.afetch("f.txt"), "v3")

    async def test_compare_and_update_stale_cas_fails_after_win(self):
        """After a CAS wins, a stale CAS with old expected value must fail."""
        cache = FileCache()
        await cache.astore("f.txt", "v1")
        await cache.acompare_and_update("f.txt", "v1", "v2")
        # Stale CAS: still expects v1
        result = await cache.acompare_and_update("f.txt", "v1", "v3")
        self.assertFalse(result)
        self.assertEqual(await cache.afetch("f.txt"), "v2")


class TestLevel6CompareAndUpdateConcurrent(unittest.IsolatedAsyncioTestCase):
    async def test_100_concurrent_cas_only_one_wins(self):
        """
        100 concurrent acompare_and_update calls all expect 'initial'.
        Only ONE should succeed (the one that acquires the lock first).
        Without proper locking, multiple could win.
        """
        cache = FileCache()
        await cache.astore("counter.txt", "initial")

        results = await asyncio.gather(
            *[cache.acompare_and_update("counter.txt", "initial", f"winner-{i}") for i in range(100)]
        )

        true_count = sum(1 for r in results if r is True)
        self.assertEqual(true_count, 1, f"Expected exactly 1 winner, got {true_count}")

        # Final content should be one of the winner values
        final = await cache.afetch("counter.txt")
        self.assertTrue(
            final.startswith("winner-"),
            f"Expected winner-N value, got: {final!r}"
        )

    async def test_stale_concurrent_cas_all_fail(self):
        """
        After the file is updated to 'new-value', 100 concurrent CAS calls
        with expected='initial' must ALL fail.
        """
        cache = FileCache()
        await cache.astore("f.txt", "initial")
        # Update to 'new-value' first
        await cache.aupdate("f.txt", "new-value")

        results = await asyncio.gather(
            *[cache.acompare_and_update("f.txt", "initial", f"attempt-{i}") for i in range(100)]
        )
        true_count = sum(1 for r in results if r is True)
        self.assertEqual(true_count, 0, "All stale CAS should fail")
        self.assertEqual(await cache.afetch("f.txt"), "new-value")

    async def test_concurrent_cas_different_files_independent(self):
        """CAS on different files should not interfere with each other."""
        cache = FileCache()
        files = [f"file{i}.txt" for i in range(20)]
        for fname in files:
            await cache.astore(fname, "original")

        tasks = [cache.acompare_and_update(fname, "original", "updated") for fname in files]
        results = await asyncio.gather(*tasks)

        self.assertEqual(len(results), 20)
        self.assertTrue(all(results), "All CAS on unique files should succeed")
        for fname in files:
            self.assertEqual(await cache.afetch(fname), "updated")

    async def test_concurrent_cas_wave_exactly_one_winner_per_wave(self):
        """
        Two sequential waves of 50 concurrent CAS each.
        Wave 1: expected='v0', new='v1' — exactly 1 winner.
        Wave 2: expected='v1', new='v2' — exactly 1 winner.
        """
        cache = FileCache()
        await cache.astore("state.txt", "v0")

        wave1 = await asyncio.gather(
            *[cache.acompare_and_update("state.txt", "v0", "v1") for _ in range(50)]
        )
        self.assertEqual(sum(wave1), 1)
        self.assertEqual(await cache.afetch("state.txt"), "v1")

        wave2 = await asyncio.gather(
            *[cache.acompare_and_update("state.txt", "v1", "v2") for _ in range(50)]
        )
        self.assertEqual(sum(wave2), 1)
        self.assertEqual(await cache.afetch("state.txt"), "v2")


class TestLevel6StoreOrUpdate(unittest.IsolatedAsyncioTestCase):
    async def test_store_or_update_new_file_returns_stored(self):
        cache = FileCache()
        result = await cache.astore_or_update("f.txt", "data")
        self.assertEqual(result, "stored")

    async def test_store_or_update_existing_file_returns_updated(self):
        cache = FileCache()
        await cache.astore("f.txt", "original")
        result = await cache.astore_or_update("f.txt", "new")
        self.assertEqual(result, "updated")

    async def test_store_or_update_creates_new_file(self):
        cache = FileCache()
        await cache.astore_or_update("f.txt", "content")
        self.assertEqual(await cache.afetch("f.txt"), "content")

    async def test_store_or_update_overwrites_existing(self):
        cache = FileCache()
        await cache.astore("f.txt", "old")
        await cache.astore_or_update("f.txt", "new")
        self.assertEqual(await cache.afetch("f.txt"), "new")

    async def test_store_or_update_returns_string(self):
        cache = FileCache()
        result = await cache.astore_or_update("f.txt", "x")
        self.assertIsInstance(result, str)

    async def test_concurrent_store_or_update_same_file_no_corruption(self):
        """
        Many concurrent astore_or_update on the same file.
        Each call must return either 'stored' or 'updated' (never corrupt).
        """
        cache = FileCache()
        results = await asyncio.gather(
            *[cache.astore_or_update("shared.txt", f"val-{i}") for i in range(100)]
        )
        # Exactly one "stored", rest "updated"
        stored_count = sum(1 for r in results if r == "stored")
        updated_count = sum(1 for r in results if r == "updated")
        self.assertEqual(stored_count, 1)
        self.assertEqual(updated_count, 99)

    async def test_concurrent_store_or_update_different_files(self):
        """astore_or_update on 50 different files concurrently — all should return 'stored'."""
        cache = FileCache()
        results = await asyncio.gather(
            *[cache.astore_or_update(f"f{i}.txt", f"v{i}") for i in range(50)]
        )
        self.assertTrue(all(r == "stored" for r in results))
        self.assertEqual(cache.size(), 50)


class TestLevel6BulkStore(unittest.IsolatedAsyncioTestCase):
    async def test_bulk_store_all_new_returns_count(self):
        cache = FileCache()
        items = [("a.txt", "A"), ("b.txt", "B"), ("c.txt", "C")]
        result = await cache.abulk_store(items)
        self.assertEqual(result, 3)

    async def test_bulk_store_creates_all_files(self):
        cache = FileCache()
        items = [("a.txt", "A"), ("b.txt", "B")]
        await cache.abulk_store(items)
        self.assertEqual(await cache.afetch("a.txt"), "A")
        self.assertEqual(await cache.afetch("b.txt"), "B")

    async def test_bulk_store_with_existing_file_returns_zero(self):
        cache = FileCache()
        await cache.astore("a.txt", "existing")
        items = [("a.txt", "A"), ("b.txt", "B")]
        result = await cache.abulk_store(items)
        self.assertEqual(result, 0)

    async def test_bulk_store_atomic_rollback_on_conflict(self):
        """If any filename exists, NONE of the new files should be stored."""
        cache = FileCache()
        await cache.astore("existing.txt", "old")
        items = [("new1.txt", "N1"), ("existing.txt", "E"), ("new2.txt", "N2")]
        await cache.abulk_store(items)
        # new1 and new2 must NOT have been stored (atomic rollback)
        self.assertEqual(await cache.afetch("new1.txt"), "")
        self.assertEqual(await cache.afetch("new2.txt"), "")
        # existing.txt must not be overwritten
        self.assertEqual(await cache.afetch("existing.txt"), "old")

    async def test_bulk_store_duplicate_within_items_returns_zero(self):
        """Duplicates within the items list itself should cause failure."""
        cache = FileCache()
        items = [("f.txt", "A"), ("f.txt", "B")]
        result = await cache.abulk_store(items)
        self.assertEqual(result, 0)
        self.assertEqual(await cache.afetch("f.txt"), "")

    async def test_bulk_store_empty_list_returns_zero(self):
        cache = FileCache()
        result = await cache.abulk_store([])
        self.assertEqual(result, 0)

    async def test_bulk_store_returns_int(self):
        cache = FileCache()
        result = await cache.abulk_store([("f.txt", "x")])
        self.assertIsInstance(result, int)

    async def test_concurrent_bulk_stores_atomic(self):
        """
        Two concurrent abulk_store calls for ('f.txt', ...) and ('f.txt', ...).
        Exactly one should win (return > 0). The other must get 0 (due to collision).
        """
        cache = FileCache()
        results = await asyncio.gather(
            cache.abulk_store([("f.txt", "batch1"), ("g.txt", "batch1-g")]),
            cache.abulk_store([("f.txt", "batch2"), ("h.txt", "batch2-h")]),
        )
        # Exactly one batch wins
        winning_count = sum(1 for r in results if r > 0)
        self.assertEqual(winning_count, 1, f"Expected 1 winning batch, got {winning_count}")
        # f.txt should exist with one of the values
        f_val = await cache.afetch("f.txt")
        self.assertIn(f_val, ["batch1", "batch2"])

    async def test_bulk_store_all_or_nothing_size_unchanged_on_failure(self):
        cache = FileCache()
        await cache.astore("blocker.txt", "x")
        initial_size = cache.size()
        items = [("new1.txt", "A"), ("blocker.txt", "B"), ("new2.txt", "C")]
        await cache.abulk_store(items)
        # Size should be unchanged since bulk failed
        self.assertEqual(cache.size(), initial_size)

    async def test_100_concurrent_bulk_stores_no_partial_writes(self):
        """
        100 concurrent abulk_store calls each trying to store ('shared.txt', ...).
        Since they all conflict on 'shared.txt', only 1 can win.
        The cache should be consistent — no partial writes.
        """
        cache = FileCache()
        batches = [
            [("shared.txt", f"val-{i}"), (f"unique-{i}.txt", f"u{i}")]
            for i in range(100)
        ]
        results = await asyncio.gather(*[cache.abulk_store(batch) for batch in batches])
        # Exactly one batch of 2 should win
        winners = [r for r in results if r > 0]
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0], 2)

    async def test_bulk_store_followed_by_reads_consistent(self):
        cache = FileCache()
        items = [(f"doc{i:02d}.txt", f"content-{i}") for i in range(10)]
        count = await cache.abulk_store(items)
        self.assertEqual(count, 10)
        reads = await asyncio.gather(*[cache.afetch(f"doc{i:02d}.txt") for i in range(10)])
        for i, val in enumerate(reads):
            self.assertEqual(val, f"content-{i}")


if __name__ == "__main__":
    unittest.main()
