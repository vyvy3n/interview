"""Replicates the assessment's tests/test_dns.py.

Single file with one TestStepN class per progressive step. Tests assert
the resolver's RESULT and the exact CALL SEQUENCE to send_query —
because the constants ROOT, COM, ANTHROPIC_NS, ... are imported from
dns_mock, the expected_log lines read like English DNS walk-throughs.

Run all tests for a step with `./test.sh N`. Run a single test with
`pytest tests/test_dns.py -k test_anthropic_com`.
"""
import os
import sys
import unittest

# Make the parent dir importable so `from solution import ...` works
# whether you run pytest from the repo root or from tests/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dns_mock import (  # noqa: E402
    ANTHROPIC_NS,
    API_ANTHROPIC_NS,
    CLOUDFLARE_NS,
    COM,
    DEAD_NS,
    DEADNS_BACKUP,
    EXAMPLE_NS,
    FASTCDN_NS,
    NET,
    ROOT,
    get_call_count,
    get_call_log,
    get_peak_in_flight,
    reset_call_counter,
    set_in_flight_hold,
)
from solution_independent import normalize, resolve, resolve_all  # noqa: E402


# ─────── Test helpers (these match the helpers visible in screenshots) ───────

def _resolve_and_log(domain_name, max_queries=15):
    """Reset the mock state, run resolve(), return (result, call_log)."""
    reset_call_counter()
    result = resolve(domain_name, max_queries=max_queries)
    return result, get_call_log()


def _assert_log_equal(tc, log, expected_log, domain_name):
    """Side-by-side comparison; on failure, format like the assessment does."""
    if log == expected_log:
        return
    lines = [
        f"Wrong calls to send_query for resolve(domain_name={domain_name!r}):",
        f"    {'expected':50s}  actual",
    ]
    n = max(len(log), len(expected_log))
    for i in range(n):
        e = expected_log[i] if i < len(expected_log) else "(end)"
        a = log[i] if i < len(log) else "(end)"
        marker = "" if e == a else "    ←"
        lines.append(f"    {str(e):50s}  {str(a)}{marker}")
    tc.fail("\n".join(lines))


# ─────── Step 0: Normalize ───────

class TestStep0(unittest.TestCase):
    """Step 0: Normalize a DNS name to lowercased form with a trailing dot."""

    def test_normalize_trailing_dot(self) -> None:
        self.assertEqual(normalize("anthropic.com."), "anthropic.com.")

    def test_normalize_no_trailing_dot(self) -> None:
        self.assertEqual(normalize("anthropic.com"), "anthropic.com.")

    def test_normalize_uppercase(self) -> None:
        self.assertEqual(normalize("ANTHROPIC.COM"), "anthropic.com.")

    def test_normalize_mixed_case_subdomain(self) -> None:
        self.assertEqual(normalize("Docs.Anthropic.Com"), "docs.anthropic.com.")


# ─────── Step 1: simple delegation ───────

class TestStep1(unittest.TestCase):
    """Step 1: simple delegation chains.

    Implement `resolve()` for the basic case: root -> TLD ->
    authoritative, all with glue.
    """

    def test_anthropic_com(self) -> None:
        """Simple three-step delegation: root -> .com TLD ->
        authoritative NS (with glue) -> A record."""
        result, log = _resolve_and_log("anthropic.com")
        expected_log = [
            ("anthropic.com.", ROOT),
            ("anthropic.com.", COM),
            ("anthropic.com.", ANTHROPIC_NS),
        ]
        _assert_log_equal(self, log, expected_log, "anthropic.com")
        self.assertEqual(result, "160.79.104.10")

    def test_case_insensitive(self) -> None:
        """ANTHROPIC.COM must resolve identically to anthropic.com (case-insensitive)."""
        result, log = _resolve_and_log("ANTHROPIC.COM")
        expected_log = [
            ("anthropic.com.", ROOT),
            ("anthropic.com.", COM),
            ("anthropic.com.", ANTHROPIC_NS),
        ]
        _assert_log_equal(self, log, expected_log, "ANTHROPIC.COM")
        self.assertEqual(result, "160.79.104.10")


# ─────── Step 2: CNAME records ───────

class TestStep2(unittest.TestCase):
    """Step 2: CNAME records (single hop and multi-hop chains)."""

    def test_single_hop_same_zone(self) -> None:
        """www.example.com CNAMEs to example.com (same zone, same authoritative server)."""
        result, log = _resolve_and_log("www.example.com")
        expected_log = [
            ("www.example.com.", ROOT),
            ("www.example.com.", COM),
            ("www.example.com.", EXAMPLE_NS),
            # CNAME to example.com → restart from root
            ("example.com.", ROOT),
            ("example.com.", COM),
            ("example.com.", EXAMPLE_NS),
        ]
        _assert_log_equal(self, log, expected_log, "www.example.com")
        self.assertEqual(result, "93.184.216.34")

    def test_two_hop_chain(self) -> None:
        """store.example.com CNAMEs to shop.fastcdn.net which CNAMEs to cdn.fastcdn.net."""
        result, log = _resolve_and_log("store.example.com")
        expected_log = [
            ("store.example.com.", ROOT),
            ("store.example.com.", COM),
            ("store.example.com.", EXAMPLE_NS),
            # CNAME to shop.fastcdn.net → restart from root
            ("shop.fastcdn.net.", ROOT),
            ("shop.fastcdn.net.", NET),
            ("shop.fastcdn.net.", FASTCDN_NS),
            # CNAME to cdn.fastcdn.net → restart from root
            ("cdn.fastcdn.net.", ROOT),
            ("cdn.fastcdn.net.", NET),
            ("cdn.fastcdn.net.", FASTCDN_NS),
        ]
        _assert_log_equal(self, log, expected_log, "store.example.com")
        self.assertEqual(result, "203.0.113.99")

    def test_direct_a_no_cname(self) -> None:
        """example.com has a direct A — no CNAME involved."""
        result, log = _resolve_and_log("example.com")
        expected_log = [
            ("example.com.", ROOT),
            ("example.com.", COM),
            ("example.com.", EXAMPLE_NS),
        ]
        _assert_log_equal(self, log, expected_log, "example.com")
        self.assertEqual(result, "93.184.216.34")


# ─────── Step 3: Missing glue records ───────

class TestStep3(unittest.TestCase):
    """Step 3: NS record with no glue — recursively resolve the NS name first."""

    def test_api_anthropic_com(self) -> None:
        """api.anthropic.com → COM_TLD says NS=gemma.ns.cloudflare.com (no glue).
        Resolver must recursively resolve gemma.ns.cloudflare.com first."""
        result, log = _resolve_and_log("api.anthropic.com")
        expected_log = [
            ("api.anthropic.com.", ROOT),
            ("api.anthropic.com.", COM),
            # COM_TLD response has no glue → recursively resolve gemma.ns.cloudflare.com
            ("gemma.ns.cloudflare.com.", ROOT),
            ("gemma.ns.cloudflare.com.", COM),
            ("gemma.ns.cloudflare.com.", CLOUDFLARE_NS),
            # Now we have API_ANTHROPIC_NS's IP, continue resolving api.anthropic.com
            ("api.anthropic.com.", API_ANTHROPIC_NS),
        ]
        _assert_log_equal(self, log, expected_log, "api.anthropic.com")
        self.assertEqual(result, "104.16.1.1")


# ─────── Step 4: Error handling and NS fallback ───────

class TestStep4(unittest.TestCase):
    """Step 4: NXDOMAIN/REFUSED handling + NS fallback when first NS fails."""

    def test_ns_fallback_on_refused(self) -> None:
        """deadns.com: first NS (DEAD_NS) returns REFUSED; fall back to second NS (DEADNS_BACKUP)."""
        result, log = _resolve_and_log("deadns.com")
        expected_log = [
            ("deadns.com.", ROOT),
            ("deadns.com.", COM),
            ("deadns.com.", DEAD_NS),         # REFUSED
            ("deadns.com.", DEADNS_BACKUP),   # succeeds
        ]
        _assert_log_equal(self, log, expected_log, "deadns.com")
        self.assertEqual(result, "192.0.2.99")

    def test_nxdomain_returns_none(self) -> None:
        result, log = _resolve_and_log("missing.example")
        expected_log = [
            ("missing.example.", ROOT),
        ]
        _assert_log_equal(self, log, expected_log, "missing.example")
        self.assertIsNone(result)

    def test_all_ns_refused(self) -> None:
        """broken.com: every NS returns REFUSED (no fallback works) → None."""
        result, log = _resolve_and_log("broken.com")
        expected_log = [
            ("broken.com.", ROOT),
            ("broken.com.", COM),
            ("broken.com.", DEAD_NS),         # REFUSED
            ("broken.com.", "192.0.2.99"),    # also REFUSED
        ]
        _assert_log_equal(self, log, expected_log, "broken.com")
        self.assertIsNone(result)


# ─────── Step 5: Cycle handling via max_queries ───────

class TestStep5(unittest.TestCase):
    """Step 5: cycle detection — return None after max_queries calls to send_query."""

    def test_cname_loop_returns_none(self) -> None:
        """loop-a.test → CNAME loop-b.test → CNAME loop-a.test → ..."""
        reset_call_counter()
        result = resolve("loop-a.test", max_queries=15)
        self.assertIsNone(result)
        self.assertLessEqual(get_call_count(), 15,
            f"Resolver made {get_call_count()} send_query calls (limit was 15)")

    def test_max_queries_respected_on_clean_resolve(self) -> None:
        """A 3-hop resolve must use far fewer than max_queries calls."""
        reset_call_counter()
        result = resolve("anthropic.com", max_queries=15)
        self.assertEqual(result, "160.79.104.10")
        self.assertLess(get_call_count(), 15)

    def test_low_max_queries_kills_resolve(self) -> None:
        """max_queries=2 against a 3-hop chain must return None."""
        reset_call_counter()
        result = resolve("anthropic.com", max_queries=2)
        self.assertIsNone(result)


# ─────── Step 6: Cached batch resolution ───────

class TestStep6(unittest.TestCase):
    """Step 6: resolve_all() with per-call (name, server) cache."""

    def test_keys_match_input_form(self) -> None:
        reset_call_counter()
        result = resolve_all(["Anthropic.COM", "anthropic.com."])
        self.assertEqual(result, {
            "Anthropic.COM":  "160.79.104.10",
            "anthropic.com.": "160.79.104.10",
        })

    def test_duplicate_inputs_only_query_once(self) -> None:
        reset_call_counter()
        resolve_all(["anthropic.com", "anthropic.com", "anthropic.com"])
        # 3 hops, cached on the first → 3 total send_query calls.
        self.assertEqual(get_call_count(), 3)

    def test_overlapping_paths_share_cache(self) -> None:
        reset_call_counter()
        result = resolve_all(["www.example.com", "example.com"])
        self.assertEqual(result["www.example.com"], "93.184.216.34")
        self.assertEqual(result["example.com"],     "93.184.216.34")
        # www.example.com path: 6 unique queries (3 for www, 3 for example after CNAME).
        # example.com path: shares the last 3 (example.com queries) — so 0 new queries.
        # Total: 6.
        self.assertEqual(get_call_count(), 6)

    def test_empty_input_returns_empty_dict(self) -> None:
        reset_call_counter()
        self.assertEqual(resolve_all([]), {})

    def test_cache_scoped_to_each_call(self) -> None:
        """Cache must NOT survive across resolve_all() invocations."""
        reset_call_counter()
        resolve_all(["anthropic.com"])
        first = get_call_count()
        resolve_all(["anthropic.com"])
        self.assertEqual(get_call_count(), 2 * first)

    def test_nxdomain_responses_are_cached(self) -> None:
        """NXDOMAIN responses must be cached (Step 6 spec bullet)."""
        reset_call_counter()
        result = resolve_all(["missing.example", "Missing.Example"])
        self.assertIsNone(result["missing.example"])
        self.assertIsNone(result["Missing.Example"])
        self.assertEqual(get_call_count(), 1,
            "NXDOMAIN must be cached — duplicate name should not re-query.")

    def test_refused_responses_are_cached(self) -> None:
        """REFUSED responses must be cached (Step 6 spec bullet)."""
        reset_call_counter()
        result = resolve_all(["broken.com", "Broken.COM"])
        self.assertIsNone(result["broken.com"])
        self.assertIsNone(result["Broken.COM"])
        # broken.com walk: root, com_tld, ns1 (REFUSED), ns2 (REFUSED) = 4 queries.
        # If REFUSED weren't cached, the second copy would re-walk = 8 queries.
        self.assertEqual(get_call_count(), 4)

    def test_max_queries_is_per_domain(self) -> None:
        """Per-spec: max_queries is the limit per domain, not per batch."""
        reset_call_counter()
        result = resolve_all(["anthropic.com.", "Anthropic.COM"], max_queries=3)
        # Per-batch: second domain would have 0 budget after first uses 3 → fail.
        # Per-domain: each starts fresh with 3 → both succeed.
        self.assertEqual(result["anthropic.com."], "160.79.104.10")
        self.assertEqual(result["Anthropic.COM"], "160.79.104.10")

    def test_cache_hits_count_against_max_queries(self) -> None:
        """Per-spec: 'A cache hit does not call send_query, but still counts
        against the limit for that domain.'"""
        reset_call_counter()
        result = resolve_all(["anthropic.com", "Anthropic.COM"], max_queries=2)
        # Both must fail. If cache hits didn't count, the second resolve
        # could use cached entries and complete via 1 real query.
        self.assertIsNone(result["anthropic.com"])
        self.assertIsNone(result["Anthropic.COM"])


# ─────── Step 7: Parallel resolution ───────

class TestStep7(unittest.TestCase):
    """Step 7: bounded concurrency + single-flight in-flight dedup."""

    def test_in_flight_never_exceeds_max_workers(self) -> None:
        reset_call_counter()
        set_in_flight_hold(0.02)  # force overlap
        resolve_all(
            ["www.example.com", "example.com", "store.example.com"],
            max_workers=2,
        )
        peak = get_peak_in_flight()
        self.assertLessEqual(peak, 2,
            f"Concurrency cap violated — peak in-flight was {peak} (limit=2)")

    def test_concurrent_duplicate_resolves_share_in_flight(self) -> None:
        """Per-spec: 'If a query is already in-flight from another domain's
        resolution, wait for it rather than sending a duplicate.'"""
        reset_call_counter()
        set_in_flight_hold(0.05)
        result = resolve_all(["anthropic.com", "Anthropic.COM."], max_workers=4)
        self.assertEqual(result["anthropic.com"], "160.79.104.10")
        self.assertEqual(result["Anthropic.COM."], "160.79.104.10")
        # Without single-flight dedup: 6 queries (3 per domain). With: 3.
        self.assertEqual(get_call_count(), 3,
            f"In-flight dedup violated — got {get_call_count()} calls, expected 3")

    def test_concurrent_independent_domains(self) -> None:
        """Independent domains (no overlapping path) should still complete correctly."""
        reset_call_counter()
        result = resolve_all(["anthropic.com", "deadns.com"], max_workers=2)
        self.assertEqual(result["anthropic.com"], "160.79.104.10")
        self.assertEqual(result["deadns.com"], "192.0.2.99")

    def test_one_failure_does_not_block_others(self) -> None:
        reset_call_counter()
        result = resolve_all(
            ["anthropic.com", "missing.example", "example.com"],
            max_workers=3,
        )
        self.assertEqual(result["anthropic.com"],  "160.79.104.10")
        self.assertEqual(result["example.com"],    "93.184.216.34")
        self.assertIsNone(result["missing.example"])


if __name__ == "__main__":
    unittest.main()
