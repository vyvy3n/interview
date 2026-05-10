"""Level 1 — basic delegation: root → TLD → authoritative, with glue."""
import unittest

from _fixtures import SCENARIO_BASIC
from dns_mock import install_scenario, query_count
from solution import normalize, resolve


class TestNormalize(unittest.TestCase):
    def test_lowercase(self):
        self.assertEqual(normalize("Anthropic.COM"), "anthropic.com.")

    def test_already_normalized(self):
        self.assertEqual(normalize("anthropic.com."), "anthropic.com.")

    def test_no_trailing_dot(self):
        self.assertEqual(normalize("anthropic.com"), "anthropic.com.")

    def test_subdomain(self):
        self.assertEqual(normalize("Docs.Anthropic.COM"), "docs.anthropic.com.")

    def test_uppercase_with_dot(self):
        self.assertEqual(normalize("ANTHROPIC.COM."), "anthropic.com.")


class TestBasicDelegation(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_BASIC)

    def test_resolves_anthropic_com(self):
        self.assertEqual(resolve("anthropic.com"), "160.79.104.10")

    def test_resolves_uppercase(self):
        self.assertEqual(resolve("ANTHROPIC.COM"), "160.79.104.10")

    def test_resolves_with_trailing_dot(self):
        self.assertEqual(resolve("anthropic.com."), "160.79.104.10")

    def test_uses_exactly_three_queries(self):
        # root → TLD → authoritative — three send_query calls, no more.
        resolve("anthropic.com")
        self.assertEqual(query_count(), 3)


if __name__ == "__main__":
    unittest.main()
