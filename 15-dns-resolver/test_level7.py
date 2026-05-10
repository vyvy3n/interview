"""Level 7 — bounded concurrency for resolve_all()."""
import threading
import time
import unittest

from _fixtures import SCENARIO_BASIC, scenario_batch_overlap
from dns_mock import install_scenario, query_count, send_query
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
        # Sleep so multiple workers genuinely overlap.
        if self.hold_time:
            time.sleep(self.hold_time)
        with self.lock:
            self.in_flight -= 1


class TestConcurrencyCap(unittest.TestCase):
    def test_in_flight_never_exceeds_max_workers(self):
        tracker = _InFlightTracker(hold_time=0.02)
        install_scenario(scenario_batch_overlap(), observer=tracker)
        domains = [
            "www.example.com",
            "api.example.com",
            "cdn.example.com",
            "Www.Example.com",   # cache hit → should not consume budget
            "API.example.com",   # cache hit
        ]
        result = resolve_all(domains, max_workers=2)
        self.assertEqual(result["www.example.com"], "93.184.216.1")
        self.assertLessEqual(tracker.peak, 2,
            f"Concurrency cap violated — peak in-flight was {tracker.peak} (limit=2)")


class TestConcurrencyDedupes(unittest.TestCase):
    def test_dedup_still_applies_with_concurrency(self):
        install_scenario(scenario_batch_overlap())
        resolve_all(
            ["www.example.com", "api.example.com", "cdn.example.com"],
            max_workers=3,
        )
        self.assertEqual(query_count(), 9)


class TestConcurrencyErrorIsolation(unittest.TestCase):
    def test_one_failure_does_not_block_others(self):
        scenario = scenario_batch_overlap()
        install_scenario(scenario, observer=None)
        result = resolve_all(
            [
                "www.example.com",
                "doesnotexist.invalid",  # unknown → REFUSED everywhere → None
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
