"""Level 7 — Parallel resolution.

Tests cover every spec bullet from Step 7:
  - At most max_workers (default 5) calls to send_query in flight at any time.
  - If a query is already in-flight from another domain, wait for it rather
    than sending a duplicate (single-flight / request coalescing).
"""
import threading
import time
import unittest

from _fixtures import SCENARIO_BASIC, scenario_batch_overlap
from dns_mock import install_scenario, query_count
from solution import resolve_all


class _InFlightTracker:
    """Wrap send_query to record max in-flight count for assertions."""

    def __init__(self, hold_time: float = 0.0):
        self.in_flight = 0
        self.peak = 0
        self.lock = threading.Lock()
        self.hold_time = hold_time

    def __call__(self, name: str, server_ip: str):
        with self.lock:
            self.in_flight += 1
            self.peak = max(self.peak, self.in_flight)
        if self.hold_time:
            time.sleep(self.hold_time)
        with self.lock:
            self.in_flight -= 1


class TestConcurrencyCap(unittest.TestCase):
    def test_in_flight_never_exceeds_max_workers(self):
        tracker = _InFlightTracker(hold_time=0.02)
        install_scenario(scenario_batch_overlap(), observer=tracker)
        result = resolve_all(
            [
                "www.example.com",
                "api.example.com",
                "cdn.example.com",
                "Www.Example.com",   # cache hit → should not consume budget
                "API.example.com",   # cache hit
            ],
            max_workers=2,
        )
        self.assertEqual(result["www.example.com"], "93.184.216.1")
        self.assertLessEqual(tracker.peak, 2,
            f"Concurrency cap violated — peak in-flight was {tracker.peak} (limit=2)")


class TestConcurrencyDedupesDuplicateInputs(unittest.TestCase):
    def test_dedup_via_cache_with_concurrency(self):
        install_scenario(scenario_batch_overlap())
        resolve_all(
            ["www.example.com", "api.example.com", "cdn.example.com"],
            max_workers=3,
        )
        # 3 unique chains × 3 hops each = 9 unique (name, server) pairs.
        self.assertEqual(query_count(), 9)


class TestInFlightSingleFlight(unittest.TestCase):
    """Per Step 7 spec: 'If a query is already in-flight from another
    domain's resolution, wait for it rather than sending a duplicate.'"""

    def test_concurrent_duplicate_resolves_share_in_flight_queries(self):
        # Hold time forces both resolves to overlap on the same (name, server)
        # queries simultaneously — without single-flight dedup, we'd see 6
        # send_query calls (3 per domain). With dedup, we see 3.
        tracker = _InFlightTracker(hold_time=0.05)
        install_scenario(SCENARIO_BASIC, observer=tracker)
        result = resolve_all(
            ["anthropic.com", "Anthropic.COM."],   # both normalize identically
            max_workers=4,                          # plenty of capacity to race
        )
        self.assertEqual(result["anthropic.com"], "160.79.104.10")
        self.assertEqual(result["Anthropic.COM."], "160.79.104.10")
        self.assertEqual(query_count(), 3,
            f"In-flight dedup violated — got {query_count()} send_query calls, "
            "expected 3 (the second resolve must wait on the first's queries)")

    def test_concurrent_overlapping_paths_share_in_flight(self):
        # Three domains share the same root + .com TLD path. With slow queries,
        # the root query and the com TLD query (one per name) should each only
        # happen once even if all three resolves race for them.
        # NOTE: each domain still has its OWN authoritative-server query
        # (different (name, server) pair), so we can't assert <9 queries —
        # we only assert no DUPLICATE queries (which would otherwise happen
        # under racing without dedup).
        tracker = _InFlightTracker(hold_time=0.03)
        install_scenario(scenario_batch_overlap(), observer=tracker)
        result = resolve_all(
            ["www.example.com", "api.example.com", "cdn.example.com"],
            max_workers=5,
        )
        self.assertEqual(result["www.example.com"], "93.184.216.1")
        self.assertEqual(result["api.example.com"], "93.184.216.2")
        self.assertEqual(result["cdn.example.com"], "93.184.216.3")
        # Each domain has 3 unique (name, server) keys; nothing overlaps.
        self.assertEqual(query_count(), 9)


class TestConcurrencyErrorIsolation(unittest.TestCase):
    def test_one_failure_does_not_block_others(self):
        install_scenario(scenario_batch_overlap())
        result = resolve_all(
            [
                "www.example.com",
                "doesnotexist.invalid",   # unknown → REFUSED everywhere → None
                "api.example.com",
            ],
            max_workers=3,
        )
        self.assertEqual(result["www.example.com"], "93.184.216.1")
        self.assertEqual(result["api.example.com"], "93.184.216.2")
        self.assertIsNone(result["doesnotexist.invalid"])


class TestConcurrencyResultKeys(unittest.TestCase):
    def test_result_keys_preserved_under_concurrency(self):
        install_scenario(SCENARIO_BASIC)
        result = resolve_all(["Anthropic.COM"], max_workers=4)
        self.assertEqual(list(result.keys()), ["Anthropic.COM"])


if __name__ == "__main__":
    unittest.main()
