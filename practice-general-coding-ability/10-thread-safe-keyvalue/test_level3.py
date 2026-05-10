"""
Level 3 tests — TTL / expiration with explicit timestamps
Run: python3 test_level3.py
"""

import unittest
from solution import KVStore


class TestLevel3PutWithTTL(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_put_with_ttl_stores_value(self):
        self.kv.put_with_ttl("k", "v", ttl=10, now=0)
        self.assertEqual(self.kv.get("k"), "v")

    def test_put_with_ttl_overwrites_existing(self):
        self.kv.put("k", "old")
        self.kv.put_with_ttl("k", "new", ttl=5, now=0)
        self.assertEqual(self.kv.get("k"), "new")

    def test_put_with_ttl_overwrites_another_ttl_entry(self):
        self.kv.put_with_ttl("k", "first", ttl=100, now=0)
        self.kv.put_with_ttl("k", "second", ttl=5, now=0)
        self.assertEqual(self.kv.get_at("k", now=4), "second")
        self.assertEqual(self.kv.get_at("k", now=5), "")


class TestLevel3GetAt(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_get_at_before_expiry(self):
        self.kv.put_with_ttl("k", "v", ttl=10, now=100)
        # expiry = 110; now=109 < 110 → alive
        self.assertEqual(self.kv.get_at("k", now=109), "v")

    def test_get_at_at_exact_expiry_is_expired(self):
        self.kv.put_with_ttl("k", "v", ttl=10, now=100)
        # expiry = 110; now=110 → expired (expiry <= now)
        self.assertEqual(self.kv.get_at("k", now=110), "")

    def test_get_at_after_expiry_is_expired(self):
        self.kv.put_with_ttl("k", "v", ttl=10, now=100)
        self.assertEqual(self.kv.get_at("k", now=200), "")

    def test_get_at_missing_key(self):
        self.assertEqual(self.kv.get_at("missing", now=0), "")

    def test_get_at_no_ttl_key_never_expires(self):
        self.kv.put("k", "permanent")
        self.assertEqual(self.kv.get_at("k", now=999999), "permanent")

    def test_plain_get_ignores_ttl(self):
        """Critical: get() must NOT check TTL."""
        self.kv.put_with_ttl("k", "v", ttl=10, now=0)
        # Expired at now=10, but plain get() should still return value
        self.assertEqual(self.kv.get("k"), "v")
        self.assertEqual(self.kv.get_at("k", now=10), "")
        self.assertEqual(self.kv.get("k"), "v")  # still returns raw value

    def test_plain_put_clears_ttl(self):
        """put() after put_with_ttl makes the entry permanent."""
        self.kv.put_with_ttl("k", "v", ttl=5, now=0)
        self.kv.put("k", "permanent")
        # Would have expired at now=5, but TTL was cleared by plain put
        self.assertEqual(self.kv.get_at("k", now=5), "permanent")
        self.assertEqual(self.kv.get_at("k", now=100), "permanent")


class TestLevel3CleanupExpired(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_cleanup_removes_expired(self):
        self.kv.put_with_ttl("a", "1", ttl=5, now=0)   # expiry=5
        self.kv.put_with_ttl("b", "2", ttl=10, now=0)  # expiry=10
        count = self.kv.cleanup_expired(now=5)
        self.assertEqual(count, 1)  # "a" expired (5 <= 5)
        self.assertEqual(self.kv.count(), 1)  # "b" survives

    def test_cleanup_does_not_remove_non_expired(self):
        self.kv.put_with_ttl("a", "1", ttl=10, now=0)  # expiry=10
        self.kv.put_with_ttl("b", "2", ttl=20, now=0)  # expiry=20
        count = self.kv.cleanup_expired(now=5)
        self.assertEqual(count, 0)

    def test_cleanup_does_not_remove_permanent_entries(self):
        self.kv.put("perm", "forever")
        self.kv.put_with_ttl("temp", "v", ttl=1, now=0)
        count = self.kv.cleanup_expired(now=100)
        self.assertEqual(count, 1)
        self.assertEqual(self.kv.get("perm"), "forever")

    def test_cleanup_returns_zero_when_nothing_to_remove(self):
        self.kv.put("k", "v")
        count = self.kv.cleanup_expired(now=999)
        self.assertEqual(count, 0)

    def test_cleanup_removes_multiple(self):
        for i in range(5):
            self.kv.put_with_ttl(f"k{i}", str(i), ttl=10, now=0)  # all expire=10
        self.kv.put("permanent", "p")
        count = self.kv.cleanup_expired(now=10)
        self.assertEqual(count, 5)
        self.assertEqual(self.kv.count(), 1)

    def test_cleanup_idempotent(self):
        self.kv.put_with_ttl("k", "v", ttl=5, now=0)
        first = self.kv.cleanup_expired(now=10)
        second = self.kv.cleanup_expired(now=10)
        self.assertEqual(first, 1)
        self.assertEqual(second, 0)

    def test_cleanup_returns_int(self):
        result = self.kv.cleanup_expired(now=0)
        self.assertIsInstance(result, int)

    def test_boundary_expiry_le_now(self):
        """expiry <= now is expired."""
        self.kv.put_with_ttl("a", "v", ttl=7, now=3)  # expiry=10
        self.assertEqual(self.kv.cleanup_expired(now=9), 0)  # 10 > 9, alive
        self.assertEqual(self.kv.cleanup_expired(now=10), 1)  # 10 <= 10, gone


class TestLevel3BackwardsCompat(unittest.TestCase):
    def test_l1_l2_still_work(self):
        kv = KVStore()
        kv.put("x", "hello")
        self.assertEqual(kv.get("x"), "hello")
        kv.put("y", "world")
        self.assertEqual(kv.multi_get(["x", "y"]), ["hello", "world"])
        self.assertEqual(kv.count(), 2)
        kv.delete("x")
        self.assertEqual(kv.count(), 1)


if __name__ == "__main__":
    unittest.main()
