"""Level 4 — NS fallback + status code handling (NXDOMAIN, REFUSED)."""
import unittest

from _fixtures import (
    scenario_all_ns_fail,
    scenario_ns_fallback_no_glue,
    scenario_ns_fallback_refused,
    scenario_nxdomain,
)
from dns_mock import install_scenario
from solution import resolve


class TestNsFallbackOnRefused(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_ns_fallback_refused())

    def test_falls_back_to_second_ns(self):
        # First NS returns REFUSED — second NS has the answer.
        self.assertEqual(resolve("deadns.com"), "192.0.2.99")


class TestNsFallbackOnMissingGlue(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_ns_fallback_no_glue())

    def test_falls_back_when_first_ns_unresolvable(self):
        # First NS has no glue and its name can't be resolved (NXDOMAIN at root).
        # Second NS has glue and works.
        self.assertEqual(resolve("split.com"), "192.0.2.42")


class TestNxdomain(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_nxdomain())

    def test_nxdomain_returns_none(self):
        self.assertIsNone(resolve("missing.example"))


class TestAllNsFail(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_all_ns_fail())

    def test_returns_none_when_no_ns_works(self):
        self.assertIsNone(resolve("broken.com"))


if __name__ == "__main__":
    unittest.main()
