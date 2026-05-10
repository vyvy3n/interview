"""Level 3 — missing glue records (recursive NS-name resolution)."""
import unittest

from _fixtures import scenario_missing_glue
from dns_mock import install_scenario
from solution import resolve


class TestMissingGlue(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_missing_glue())

    def test_resolves_via_recursive_ns_lookup(self):
        # api.anthropic.com → NS gemma.ns.cloudflare.com (no glue)
        # Resolver must recursively resolve the NS name first, then continue.
        self.assertEqual(resolve("api.anthropic.com"), "104.16.1.1")


if __name__ == "__main__":
    unittest.main()
