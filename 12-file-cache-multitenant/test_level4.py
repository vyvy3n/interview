"""
Level 4 tests — Multi-tenant file cache
Run: python3 test_level4.py
"""

import unittest
from solution import FileCache


class TestLevel4RegisterTenant(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_register_new_tenant_returns_true(self):
        self.assertTrue(self.cache.register_tenant("alice", 10))

    def test_register_duplicate_tenant_returns_false(self):
        self.cache.register_tenant("alice", 10)
        self.assertFalse(self.cache.register_tenant("alice", 20))

    def test_register_multiple_distinct_tenants(self):
        self.assertTrue(self.cache.register_tenant("alice", 5))
        self.assertTrue(self.cache.register_tenant("bob", 3))
        self.assertTrue(self.cache.register_tenant("carol", 1))

    def test_register_returns_bool(self):
        result = self.cache.register_tenant("t1", 10)
        self.assertIsInstance(result, bool)


class TestLevel4TenantIsolation(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()
        self.cache.register_tenant("alice", 10)
        self.cache.register_tenant("bob", 10)

    def test_tenant_files_isolated(self):
        self.cache.tenant_store("alice", "notes.txt", "alice's notes")
        self.cache.tenant_store("bob", "notes.txt", "bob's notes")
        self.assertEqual(self.cache.tenant_fetch("alice", "notes.txt"), "alice's notes")
        self.assertEqual(self.cache.tenant_fetch("bob", "notes.txt"), "bob's notes")

    def test_tenant_remove_does_not_affect_other_tenant(self):
        self.cache.tenant_store("alice", "shared.txt", "alice copy")
        self.cache.tenant_store("bob", "shared.txt", "bob copy")
        self.cache.tenant_remove("alice", "shared.txt")
        self.assertEqual(self.cache.tenant_fetch("alice", "shared.txt"), "")
        self.assertEqual(self.cache.tenant_fetch("bob", "shared.txt"), "bob copy")

    def test_tenant_update_does_not_affect_other_tenant(self):
        self.cache.tenant_store("alice", "f.txt", "original")
        self.cache.tenant_store("bob", "f.txt", "original")
        self.cache.tenant_update("alice", "f.txt", "alice-updated")
        self.assertEqual(self.cache.tenant_fetch("bob", "f.txt"), "original")

    def test_tenant_size_counts_only_own_files(self):
        self.cache.tenant_store("alice", "a.txt", "A")
        self.cache.tenant_store("alice", "b.txt", "B")
        self.cache.tenant_store("bob", "x.txt", "X")
        self.assertEqual(self.cache.tenant_size("alice"), 2)
        self.assertEqual(self.cache.tenant_size("bob"), 1)

    def test_tenant_fetch_by_prefix_scoped_to_tenant(self):
        self.cache.tenant_store("alice", "log_a.txt", "a")
        self.cache.tenant_store("alice", "log_b.txt", "b")
        self.cache.tenant_store("bob", "log_c.txt", "c")
        result = self.cache.tenant_fetch_by_prefix("alice", "log_")
        self.assertEqual(result, ["log_a.txt", "log_b.txt"])


class TestLevel4Quota(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_tenant_cannot_exceed_quota(self):
        self.cache.register_tenant("t1", 2)
        self.assertTrue(self.cache.tenant_store("t1", "f1.txt", "A"))
        self.assertTrue(self.cache.tenant_store("t1", "f2.txt", "B"))
        # Third store should be rejected by quota
        self.assertFalse(self.cache.tenant_store("t1", "f3.txt", "C"))
        self.assertEqual(self.cache.tenant_size("t1"), 2)

    def test_quota_not_consumed_by_failed_store(self):
        self.cache.register_tenant("t1", 2)
        self.cache.tenant_store("t1", "f1.txt", "A")
        self.cache.tenant_store("t1", "f2.txt", "B")
        # This should fail (over quota)
        self.cache.tenant_store("t1", "f3.txt", "C")
        # Quota usage is still 2
        self.assertEqual(self.cache.tenant_size("t1"), 2)

    def test_quota_freed_after_remove(self):
        self.cache.register_tenant("t1", 2)
        self.cache.tenant_store("t1", "f1.txt", "A")
        self.cache.tenant_store("t1", "f2.txt", "B")
        self.cache.tenant_remove("t1", "f1.txt")
        # Now quota has space again
        self.assertTrue(self.cache.tenant_store("t1", "f3.txt", "C"))

    def test_update_does_not_consume_extra_quota(self):
        self.cache.register_tenant("t1", 2)
        self.cache.tenant_store("t1", "f1.txt", "A")
        self.cache.tenant_store("t1", "f2.txt", "B")
        # Update should work and NOT increase quota usage
        self.assertTrue(self.cache.tenant_update("t1", "f1.txt", "A-updated"))
        self.assertEqual(self.cache.tenant_size("t1"), 2)

    def test_different_tenants_have_independent_quotas(self):
        self.cache.register_tenant("big", 100)
        self.cache.register_tenant("small", 1)
        for i in range(50):
            self.cache.tenant_store("big", f"f{i}.txt", "data")
        self.assertTrue(self.cache.tenant_store("small", "only.txt", "data"))
        self.assertFalse(self.cache.tenant_store("small", "overflow.txt", "data"))
        self.assertEqual(self.cache.tenant_size("big"), 50)
        self.assertEqual(self.cache.tenant_size("small"), 1)


class TestLevel4BackwardCompatibility(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_l1_store_still_works(self):
        self.assertTrue(self.cache.store("f.txt", "data"))
        self.assertEqual(self.cache.fetch("f.txt"), "data")

    def test_l1_global_and_tenant_are_isolated(self):
        self.cache.store("shared.txt", "global")
        self.cache.register_tenant("alice", 10)
        self.cache.tenant_store("alice", "shared.txt", "alice")
        self.assertEqual(self.cache.fetch("shared.txt"), "global")
        self.assertEqual(self.cache.tenant_fetch("alice", "shared.txt"), "alice")

    def test_l2_methods_still_work(self):
        self.cache.store("a.txt", "aaa")
        self.cache.store("b.txt", "bb")
        self.cache.update("a.txt", "x")
        self.assertEqual(self.cache.get_total_size(), len("x") + len("bb"))
        self.assertEqual(self.cache.fetch_by_prefix("a"), ["a.txt"])

    def test_global_size_not_affected_by_tenant_files(self):
        self.cache.store("g.txt", "global")
        self.cache.register_tenant("t1", 10)
        self.cache.tenant_store("t1", "t.txt", "tenant")
        # global size only counts global tenant files
        self.assertEqual(self.cache.size(), 1)

    def test_l3_set_capacity_evicts_across_tenants(self):
        self.cache.register_tenant("t1", 10)
        self.cache.register_tenant("t2", 10)
        # Store files in order: global, t1, t2
        self.cache.store("g.txt", "G")
        self.cache.tenant_store("t1", "t1.txt", "T1")
        self.cache.tenant_store("t2", "t2.txt", "T2")
        # Set capacity to 2 — should evict oldest (global "g.txt")
        evicted = self.cache.set_capacity(2)
        self.assertEqual(evicted, 1)
        self.assertEqual(self.cache.fetch("g.txt"), "")

    def test_unregistered_tenant_store_returns_false(self):
        result = self.cache.tenant_store("unknown", "f.txt", "data")
        self.assertFalse(result)

    def test_unregistered_tenant_fetch_returns_empty(self):
        result = self.cache.tenant_fetch("unknown", "f.txt")
        self.assertEqual(result, "")

    def test_unregistered_tenant_size_returns_zero(self):
        result = self.cache.tenant_size("unknown")
        self.assertEqual(result, 0)


class TestLevel4LRUCrossTenantsCapacity(unittest.TestCase):
    def test_global_lru_eviction_respects_tenant_counts(self):
        cache = FileCache()
        cache.register_tenant("t1", 5)
        # Store alternating between global and t1
        cache.store("g1.txt", "G")       # global: 1
        cache.tenant_store("t1", "ta.txt", "A")   # t1: 1
        cache.tenant_store("t1", "tb.txt", "B")   # t1: 2
        # Set capacity to 2 — evict global g1 (oldest) and ta (second oldest)
        evicted = cache.set_capacity(2)
        self.assertEqual(evicted, 1)
        # g1 was evicted (LRU)
        self.assertEqual(cache.fetch("g1.txt"), "")
        # t1 tenant count decreased
        self.assertLessEqual(cache.tenant_size("t1"), 2)


if __name__ == "__main__":
    unittest.main()
