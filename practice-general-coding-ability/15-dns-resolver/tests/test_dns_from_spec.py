"""Tests derived directly from spec/levelN.md text — no reference to solution.py.

Each test cites the spec sentence(s) it's derived from. Where the spec uses a
concrete walkthrough (e.g. Level 1's anthropic.com → 160.79.104.10), the
expected_log is grounded in the spec's literal narrative. Where the spec only
describes behavior abstractly (e.g. Level 5's cycle detection), the test
asserts the abstract property (result is None, query count <= max_queries).
"""
import os
import sys
import unittest

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
from solution import normalize, resolve, resolve_all  # noqa: E402


# ─── Step 0 — Normalize ─────────────────────────────────────────
# Spec quote: "In DNS, names are case insensitive, and by convention always
# end in a trailing dot. For example, 'Anthropic.COM' normalizes to 'anthropic.com.'."

class TestStep0Normalize(unittest.TestCase):
    def test_spec_example_anthropic_com(self):
        # Spec docstring example
        self.assertEqual(normalize("Anthropic.COM"), "anthropic.com.")

    def test_spec_example_docs_anthropic(self):
        # Spec docstring example
        self.assertEqual(normalize("Docs.Anthropic.Com"), "docs.anthropic.com.")

    def test_spec_example_all_uppercase(self):
        # Spec docstring example
        self.assertEqual(normalize("ANTHROPIC.COM"), "anthropic.com.")

    def test_already_normalized_idempotent(self):
        # Implied by 'normalize' being a normal-form function
        self.assertEqual(normalize("anthropic.com."), "anthropic.com.")
        self.assertEqual(normalize(normalize("Anthropic.COM")), "anthropic.com.")


# ─── Step 1 — Annotated example ─────────────────────────────────
# Spec walks through anthropic.com ending at "we return its rdata" = "160.79.104.10".
# The walkthrough lists three send_query calls in order.

class TestStep1AnnotatedExample(unittest.TestCase):
    def test_anthropic_com_resolves_to_spec_ip(self):
        # Spec end-of-walkthrough: "we return its rdata" = 160.79.104.10
        reset_call_counter()
        self.assertEqual(resolve("anthropic.com"), "160.79.104.10")

    def test_anthropic_com_uses_three_send_query_calls(self):
        # Spec walkthrough has exactly 3 send_query calls.
        reset_call_counter()
        resolve("anthropic.com")
        self.assertEqual(get_call_count(), 3)

    def test_anthropic_com_call_sequence_matches_spec_walkthrough(self):
        # Spec: send_query("anthropic.com.", ROOT_SERVER) → delegate to .com
        #       send_query("anthropic.com.", "192.5.6.30") → delegate to ANTHROPIC_NS
        #       send_query("anthropic.com.", "108.162.192.119") → A record
        reset_call_counter()
        resolve("anthropic.com")
        self.assertEqual(get_call_log(), [
            ("anthropic.com.", ROOT),                # ROOT_SERVER
            ("anthropic.com.", "192.5.6.30"),        # COM TLD per spec
            ("anthropic.com.", "108.162.192.119"),   # ANTHROPIC_NS per spec
        ])

    def test_case_insensitive_resolves_same(self):
        # Spec says names are case-insensitive. The footer also says
        # "Check your normalization." if NXDOMAIN happens — strong hint.
        reset_call_counter()
        self.assertEqual(resolve("ANTHROPIC.COM"), "160.79.104.10")
        # And the call log should be normalized:
        self.assertTrue(all(name == "anthropic.com." for name, _ in get_call_log()))

    def test_ipv4_glue_used_not_ipv6(self):
        # Spec: "We need the one with rdtype='A' — that's the IPv4 address.
        # (The AAAA record is IPv6, which we'll ignore.)"
        # Asserted indirectly: if the resolver picks AAAA glue ("2001:db8::1"),
        # the next send_query would have a non-IP server arg and validate-fail,
        # OR (if the validator is lenient) it would be unreachable. Either way
        # the resolve would not return 160.79.104.10.
        reset_call_counter()
        self.assertEqual(resolve("anthropic.com"), "160.79.104.10")


# ─── Step 2 — CNAME records ─────────────────────────────────────
# Spec: "we have to start the process over from the root server, but instead
#        of looking for www.example.com, we're now looking for ... example.com."

class TestStep2CnameSingleHop(unittest.TestCase):
    def test_cname_restarts_from_root(self):
        # Spec: must restart from root. So resolve(www.example.com) must include
        # at minimum: query for www.example.com at ROOT, then later query for
        # example.com at ROOT.
        reset_call_counter()
        result = resolve("www.example.com")
        self.assertIsNotNone(result, "CNAME chain should resolve to an IP")
        log = get_call_log()
        # Must query www.example.com. at ROOT at some point
        self.assertIn(("www.example.com.", ROOT), log)
        # Must query example.com. at ROOT at some point (the restart)
        self.assertIn(("example.com.", ROOT), log)
        # And the example.com query at ROOT must come AFTER the www query at ROOT
        idx_www_root = log.index(("www.example.com.", ROOT))
        idx_ex_root = log.index(("example.com.", ROOT))
        self.assertLess(idx_www_root, idx_ex_root,
            "After CNAME, must restart from root for the alias name")


class TestStep2CnameMultiHop(unittest.TestCase):
    def test_multi_hop_chain_resolves(self):
        # Spec example: store.example.com → shop.fastcdn.net → cdn.fastcdn.net → A
        reset_call_counter()
        result = resolve("store.example.com")
        self.assertIsNotNone(result)

    def test_multi_hop_chain_visits_all_three_names_at_root(self):
        # Each hop in the CNAME chain restarts from root.
        reset_call_counter()
        resolve("store.example.com")
        log = get_call_log()
        self.assertIn(("store.example.com.", ROOT), log)
        self.assertIn(("shop.fastcdn.net.", ROOT), log)
        self.assertIn(("cdn.fastcdn.net.", ROOT), log)


# ─── Step 3 — Missing glue records ──────────────────────────────
# Spec: "we need to resolve gemma.ns.cloudflare.com. first (starting from the
#        root server, just like any other resolution) to get its IP, then
#        continue resolving api.anthropic.com."

class TestStep3MissingGlue(unittest.TestCase):
    def test_recursive_ns_lookup_starts_from_root(self):
        # api.anthropic.com triggers a recursive resolve of gemma.ns.cloudflare.com
        # which must start at ROOT (per spec parenthetical).
        reset_call_counter()
        result = resolve("api.anthropic.com")
        self.assertIsNotNone(result, "missing-glue path must succeed via recursive lookup")
        log = get_call_log()
        # Must have queried gemma.ns.cloudflare.com at ROOT
        self.assertIn(("gemma.ns.cloudflare.com.", ROOT), log,
            "Recursive NS resolution must start from the root server")

    def test_continues_resolving_original_after_recursive_lookup(self):
        # Spec: "then continue resolving api.anthropic.com"
        reset_call_counter()
        resolve("api.anthropic.com")
        log = get_call_log()
        # Find the index of the recursive resolution starting (gemma at ROOT)
        idx_recursive = log.index(("gemma.ns.cloudflare.com.", ROOT))
        # After that, we must have a query for api.anthropic.com at the resolved NS IP.
        # The resolved IP for gemma.ns.cloudflare.com is API_ANTHROPIC_NS in the mock.
        self.assertIn(("api.anthropic.com.", API_ANTHROPIC_NS), log)
        idx_continued = log.index(("api.anthropic.com.", API_ANTHROPIC_NS))
        self.assertGreater(idx_continued, idx_recursive,
            "Must finish recursive NS lookup before continuing original resolve")


# ─── Step 4 — Error handling and NS fallback ─────────────────────
# Spec gives concrete deadns.com example: ns1 (192.0.2.1) REFUSED → fall back to
# ns2 (192.0.2.2), which succeeds.

class TestStep4NsFallback(unittest.TestCase):
    def test_refused_falls_back_to_next_ns(self):
        # Spec walkthrough: ns1 REFUSED → fall back to ns2 (succeeds).
        reset_call_counter()
        result = resolve("deadns.com")
        self.assertIsNotNone(result, "Spec says deadns.com succeeds via second NS")
        log = get_call_log()
        # Both NS IPs must appear in the log, in order.
        self.assertIn(("deadns.com.", DEAD_NS), log,        # 192.0.2.1
                      "First NS must be queried per spec")
        self.assertIn(("deadns.com.", DEADNS_BACKUP), log,  # 192.0.2.2
                      "Second NS must be queried after first refused")
        idx1 = log.index(("deadns.com.", DEAD_NS))
        idx2 = log.index(("deadns.com.", DEADNS_BACKUP))
        self.assertLess(idx1, idx2, "Order of NS attempts must follow authority list")

    def test_nxdomain_returns_none_immediately(self):
        # Spec: "NXDOMAIN ... no point trying another NS — we can just return None."
        reset_call_counter()
        result = resolve("missing.example")
        self.assertIsNone(result)

    def test_nxdomain_does_not_continue_to_other_servers(self):
        # The spec says "no point trying another NS" — so after NXDOMAIN
        # the resolver should not make further network calls for this name.
        # (We can't test "no other NS" without a multi-NS NXDOMAIN scenario,
        # but for missing.example the count should be very small.)
        reset_call_counter()
        resolve("missing.example")
        self.assertLessEqual(get_call_count(), 3,
            "After NXDOMAIN there should be no extensive search")

    def test_all_ns_fail_returns_none(self):
        # Spec: "If all the nameservers fail to help us, we return None."
        reset_call_counter()
        result = resolve("broken.com")
        self.assertIsNone(result)


# ─── Step 5 — Cycle handling ────────────────────────────────────
# Spec: "if we haven't succeeded after max_queries calls to send_query,
#        assume we're caught in a cycle and return None."

class TestStep5Cycles(unittest.TestCase):
    def test_cname_cycle_returns_none(self):
        # The mock has a CNAME loop: loop-a.test → loop-b.test → loop-a.test
        reset_call_counter()
        result = resolve("loop-a.test", max_queries=15)
        self.assertIsNone(result)

    def test_cycle_does_not_exceed_max_queries(self):
        # Spec implies resolver self-limits — the mock raises after 500 calls,
        # so if we don't exceed max_queries, we never approach 500.
        reset_call_counter()
        resolve("loop-a.test", max_queries=15)
        self.assertLessEqual(get_call_count(), 15,
            f"Resolver made {get_call_count()} calls but max_queries was 15")

    def test_low_max_queries_kills_resolve(self):
        # If max_queries is the cap, then a value too small to complete a resolve
        # must result in None.
        reset_call_counter()
        result = resolve("anthropic.com", max_queries=2)
        self.assertIsNone(result, "max_queries=2 < 3-hop chain → must return None")

    def test_max_queries_just_enough(self):
        # Sanity: exactly enough budget allows success.
        reset_call_counter()
        result = resolve("anthropic.com", max_queries=3)
        self.assertEqual(result, "160.79.104.10")


# ─── Step 6 — Cached batch resolution ───────────────────────────

class TestStep6BatchResolve(unittest.TestCase):
    def test_returns_dict_keyed_by_input(self):
        # Spec: "return a mapping from each input domain ... to its resolved IP."
        # And: "inputs are not necessarily normalized" → keys preserve input form.
        reset_call_counter()
        result = resolve_all(["Anthropic.COM"])
        self.assertEqual(list(result.keys()), ["Anthropic.COM"])

    def test_input_form_preserved_in_result(self):
        # Spec: "(note that inputs are not necessarily normalized)" — implies
        # keys are NOT normalized; they match the input string.
        reset_call_counter()
        result = resolve_all(["Anthropic.COM", "anthropic.com."])
        # Both forms appear as separate keys, even though they normalize to the same name.
        self.assertIn("Anthropic.COM", result)
        self.assertIn("anthropic.com.", result)

    def test_no_name_server_pair_queried_twice(self):
        # Spec: "cache the result of every send_query call so that no
        #        (name, server) pair is queried twice across the batch."
        reset_call_counter()
        resolve_all(["anthropic.com", "anthropic.com", "Anthropic.COM"])
        log = get_call_log()
        self.assertEqual(len(log), len(set(log)),
            "Cache must dedupe (name, server) pairs across batch")

    def test_overlapping_paths_share_cache(self):
        # Spec: "Many domains share the same delegation path (e.g. they all
        #        query ROOT, then the .com TLD), so caching eliminates redundant work."
        reset_call_counter()
        resolve_all(["anthropic.com", "deadns.com"])
        log = get_call_log()
        # Both domains should query ROOT only once each (different names),
        # but only one of each (name, server) pair.
        self.assertEqual(len(log), len(set(log)))

    def test_nxdomain_responses_are_cached(self):
        # Spec bullet: "NXDOMAIN and REFUSED responses should also be cached."
        reset_call_counter()
        resolve_all(["missing.example", "missing.example"])
        # First lookup: 1 query to ROOT (NXDOMAIN). Second: cache hit, no new query.
        self.assertEqual(get_call_count(), 1)

    def test_refused_responses_are_cached(self):
        # Spec bullet, second half: "NXDOMAIN and REFUSED responses should also be cached."
        # broken.com: 4 queries (root, com, ns1 REFUSED, ns2 REFUSED). If REFUSED
        # weren't cached, doubling the input would double the calls (8 total).
        reset_call_counter()
        resolve_all(["broken.com", "broken.com"])
        self.assertEqual(get_call_count(), 4)

    def test_cache_is_scoped_per_call(self):
        # Spec bullet: "The cache must be scoped to each resolve_all() call —
        #               not persisted globally."
        reset_call_counter()
        resolve_all(["anthropic.com"])
        first = get_call_count()
        resolve_all(["anthropic.com"])
        # Second call must do all the work again — cache did not survive.
        self.assertEqual(get_call_count(), 2 * first)

    def test_max_queries_is_per_domain(self):
        # Spec bullet: "max_queries is the limit per domain."
        # If it were per-batch: with max_queries=3 for two 3-hop domains, the
        # second would have 0 budget after first uses 3.
        # Per-domain: each starts fresh, both succeed.
        reset_call_counter()
        result = resolve_all(["anthropic.com", "Anthropic.COM"], max_queries=3)
        # If per-domain: both succeed.
        self.assertEqual(result["anthropic.com"], "160.79.104.10")
        self.assertEqual(result["Anthropic.COM"], "160.79.104.10")

    def test_cache_hit_counts_against_per_domain_limit(self):
        # Spec bullet: "A cache hit does not call send_query, but still counts
        #               against the limit for that domain."
        reset_call_counter()
        # max_queries=2 against a 3-hop chain. First fails after 2 cached calls.
        # Second resolve: if cache hits count, both fail; if not, second succeeds
        # (would only need 1 real call after 2 cache hits).
        result = resolve_all(["anthropic.com", "Anthropic.COM"], max_queries=2)
        self.assertIsNone(result["anthropic.com"])
        self.assertIsNone(result["Anthropic.COM"],
            "Cache hits must count against per-domain max_queries — "
            "second resolve should also fail.")


# ─── Step 7 — Parallel resolution ───────────────────────────────

class TestStep7Concurrency(unittest.TestCase):
    def test_in_flight_count_capped_at_max_workers(self):
        # Spec bullet: "At most max_workers (default 5) calls to send_query
        #               may be in-flight at any time."
        reset_call_counter()
        set_in_flight_hold(0.02)
        resolve_all(
            ["anthropic.com", "deadns.com", "store.example.com", "example.com"],
            max_workers=2,
        )
        self.assertLessEqual(get_peak_in_flight(), 2)

    def test_default_max_workers_is_five(self):
        # Spec bullet says "default 5". Verify by passing nothing.
        reset_call_counter()
        set_in_flight_hold(0.01)
        # 6 independent-ish domains; with default 5 we expect peak ≤ 5.
        resolve_all([
            "anthropic.com",
            "deadns.com",
            "example.com",
            "store.example.com",
            "broken.com",
            "missing.example",
        ])
        self.assertLessEqual(get_peak_in_flight(), 5)

    def test_in_flight_dedup_avoids_duplicate_calls(self):
        # Spec bullet: "If a query is already in-flight from another domain's
        #               resolution, wait for it rather than sending a duplicate."
        # Two different inputs that normalize to the same name → both need
        # the same (name, server) queries. Without dedup: 6 send_query calls.
        # With dedup: 3.
        reset_call_counter()
        set_in_flight_hold(0.05)
        result = resolve_all(["anthropic.com", "Anthropic.COM."], max_workers=4)
        self.assertEqual(result["anthropic.com"], "160.79.104.10")
        self.assertEqual(result["Anthropic.COM."], "160.79.104.10")
        self.assertEqual(get_call_count(), 3,
            "In-flight dedup must prevent duplicate send_query calls")

    def test_concurrent_failures_do_not_block_successes(self):
        # Implied by "resolve domains concurrently to complete faster" —
        # one domain failing must not deadlock or skip others.
        reset_call_counter()
        result = resolve_all(
            ["anthropic.com", "missing.example", "broken.com", "example.com"],
            max_workers=4,
        )
        self.assertEqual(result["anthropic.com"], "160.79.104.10")
        self.assertEqual(result["example.com"], "93.184.216.34")
        self.assertIsNone(result["missing.example"])
        self.assertIsNone(result["broken.com"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
