"""Level 2 — CNAME records (single-hop and multi-hop)."""
import unittest

from _fixtures import SCENARIO_CNAME_SINGLE, SCENARIO_CNAME_MULTIHOP
from dns_mock import install_scenario
from solution import resolve


class TestCnameSingleHop(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_CNAME_SINGLE)

    def test_cname_then_a(self):
        # www.example.com. is a CNAME to example.com., which has the A record.
        self.assertEqual(resolve("www.example.com"), "93.184.216.34")

    def test_direct_a_still_works(self):
        # example.com. has a direct A — no CNAME involved.
        self.assertEqual(resolve("example.com"), "93.184.216.34")


class TestCnameMultiHop(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_CNAME_MULTIHOP)

    def test_three_hop_cname(self):
        # store.example.com. -> shop.fastcdn.net. -> cdn.fastcdn.net. -> A
        self.assertEqual(resolve("store.example.com"), "203.0.113.99")


if __name__ == "__main__":
    unittest.main()
