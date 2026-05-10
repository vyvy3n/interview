"""Mock DNS — replicates the assessment-provided dns_mock.py.

Replicated from screenshots of the actual Anthropic Constellation CodeSignal.
Constants, server topology, and validation behavior match the screenshots
as closely as possible. The simulated internet is hard-coded — tests do
not install scenarios; they reset the call counter and call resolve()
against the fixed topology.
"""
import re
import threading
import time

from dns_types import DNSRecord, DNSResponse, RData, ServerIP, ZoneName


# ─────── Server IPs in our simulated internet ───────
ROOT_SERVER:      ServerIP = "198.41.0.4"            # a.root-servers.net.
COM_TLD:          ServerIP = "192.5.6.30"            # a.gtld-servers.net.
NET_TLD:          ServerIP = "192.5.6.31"            # b.gtld-servers.net.
IO_TLD:           ServerIP = "65.22.160.17"          # ns.nic.io.
EXAMPLE_NS:       ServerIP = "93.184.216.1"          # ns.example.com.
FASTCDN_NS:       ServerIP = "151.101.1.1"           # ns.fastcdn.net.
CLOUDDNS_NS:      ServerIP = "190.51.100.1"          # ns.cloudns.io.
ANTHROPIC_NS:     ServerIP = "108.162.192.119"       # isla.ns.cloudflare.com.
API_ANTHROPIC_NS: ServerIP = "172.64.34.27"          # gemma.ns.cloudflare.com.
CLOUDFLARE_NS:    ServerIP = "162.159.0.33"          # ns3.cloudflare.com.
STATUSPAGE_NS:    ServerIP = "205.251.193.185"       # ns-441.awsdns-55.com.
DEAD_NS:          ServerIP = "192.0.2.1"             # decommissioned server
DEADNS_BACKUP:    ServerIP = "192.0.2.2"             # working backup for deadns.com.

# ─────── Convenient aliases used in test expected_log lists ───────
ROOT = ROOT_SERVER
COM  = COM_TLD
NET  = NET_TLD


# ─────── Hard limit to catch infinite loops in user code ───────
QUERY_LIMIT = 500


class QueryLimitExceeded(RuntimeError):
    """Raised when send_query is called more than QUERY_LIMIT times.

    Almost certainly means the user's resolver has an infinite loop
    or is not respecting max_queries.
    """


# ─────── Validation helpers ───────
_IP_RE = re.compile(r"\d{1,3}(\.\d{1,3}){3}")
_NAME_RE = re.compile(r"[a-z0-9.\-]+\.")


def _looks_like_ip(s: str) -> bool:
    return bool(_IP_RE.fullmatch(s))


def _looks_like_normalized(s: str) -> bool:
    return bool(_NAME_RE.fullmatch(s))


# ─────── Response builders (private) ───────
def _delegate(zone: ZoneName, ns_name: str, glue_ip: ServerIP) -> DNSResponse:
    """Single-NS delegation with one matching IPv4 glue record (and IPv6 noise)."""
    return DNSResponse(
        status="NOERROR",
        answer=None,
        authority=[DNSRecord(name=zone, rdtype="NS", rdata=ns_name)],
        additional=[
            DNSRecord(name=ns_name, rdtype="AAAA", rdata="2001:db8::1"),
            DNSRecord(name=ns_name, rdtype="A",    rdata=glue_ip),
        ],
    )


def _delegate_no_glue(zone: ZoneName, ns_name: str) -> DNSResponse:
    """Single-NS delegation with no glue — caller must recursively resolve ns_name."""
    return DNSResponse(
        status="NOERROR",
        answer=None,
        authority=[DNSRecord(name=zone, rdtype="NS", rdata=ns_name)],
        additional=[],
    )


def _delegate_two_ns(
    zone: ZoneName,
    ns1_name: str, ns1_ip: ServerIP,
    ns2_name: str, ns2_ip: ServerIP,
) -> DNSResponse:
    """Two-NS delegation, both with glue."""
    return DNSResponse(
        status="NOERROR",
        answer=None,
        authority=[
            DNSRecord(name=zone, rdtype="NS", rdata=ns1_name),
            DNSRecord(name=zone, rdtype="NS", rdata=ns2_name),
        ],
        additional=[
            DNSRecord(name=ns1_name, rdtype="AAAA", rdata="2001:db8::1"),
            DNSRecord(name=ns1_name, rdtype="A",    rdata=ns1_ip),
            DNSRecord(name=ns2_name, rdtype="AAAA", rdata="2001:db8::2"),
            DNSRecord(name=ns2_name, rdtype="A",    rdata=ns2_ip),
        ],
    )


def _answer_a(name: ZoneName, ip: ServerIP) -> DNSResponse:
    return DNSResponse(
        status="NOERROR",
        answer=DNSRecord(name=name, rdtype="A", rdata=ip),
        authority=[],
        additional=[],
    )


def _answer_cname(name: ZoneName, alias: ZoneName) -> DNSResponse:
    return DNSResponse(
        status="NOERROR",
        answer=DNSRecord(name=name, rdtype="CNAME", rdata=alias),
        authority=[],
        additional=[],
    )


_NXDOMAIN = DNSResponse(status="NXDOMAIN", answer=None, authority=[], additional=[])
_REFUSED  = DNSResponse(status="REFUSED",  answer=None, authority=[], additional=[])


# ─────── The simulated internet: ZONES[server_ip][normalized_name] = response ───────
ZONES: "dict[ServerIP, dict[ZoneName, DNSResponse]]" = {
    ROOT_SERVER: {
        # .com TLD delegations
        "anthropic.com.":     _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "api.anthropic.com.": _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "www.example.com.":   _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "example.com.":       _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "store.example.com.": _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "deadns.com.":        _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "broken.com.":        _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        # NS-name lookups (recursive, must restart from root)
        "gemma.ns.cloudflare.com.": _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "ns.cloudflare.com.":       _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        # .net TLD delegations
        "shop.fastcdn.net.": _delegate("net.", "b.gtld-servers.net.", NET_TLD),
        "cdn.fastcdn.net.":  _delegate("net.", "b.gtld-servers.net.", NET_TLD),
        # NXDOMAIN
        "missing.example.": _NXDOMAIN,
        "doesnotexist.invalid.": _NXDOMAIN,
        # CNAME loop
        "loop-a.test.": _delegate("com.", "a.gtld-servers.net.", COM_TLD),
        "loop-b.test.": _delegate("com.", "a.gtld-servers.net.", COM_TLD),
    },

    COM_TLD: {
        # Anthropic
        "anthropic.com.":     _delegate("anthropic.com.", "isla.ns.cloudflare.com.", ANTHROPIC_NS),
        "api.anthropic.com.": _delegate_no_glue("api.anthropic.com.", "gemma.ns.cloudflare.com."),
        # Example.com — both names point to EXAMPLE_NS
        "www.example.com.":   _delegate("example.com.", "ns.example.com.", EXAMPLE_NS),
        "example.com.":       _delegate("example.com.", "ns.example.com.", EXAMPLE_NS),
        "store.example.com.": _delegate("example.com.", "ns.example.com.", EXAMPLE_NS),
        # Recursive NS lookups
        "gemma.ns.cloudflare.com.": _delegate("cloudflare.com.", "ns.cloudflare.com.", CLOUDFLARE_NS),
        "ns.cloudflare.com.":       _delegate("cloudflare.com.", "ns.cloudflare.com.", CLOUDFLARE_NS),
        # deadns.com — two NS, both have glue, first one REFUSED.
        "deadns.com.": _delegate_two_ns(
            "deadns.com.",
            "ns1.deadns.com.", DEAD_NS,
            "ns2.deadns.com.", DEADNS_BACKUP,
        ),
        # broken.com — two NS, both REFUSED.
        "broken.com.": _delegate_two_ns(
            "broken.com.",
            "ns1.broken.com.", DEAD_NS,
            "ns2.broken.com.", "192.0.2.99",
        ),
        # Loop: loop-a CNAMES to loop-b which CNAMES back to loop-a
        "loop-a.test.": _delegate("test.", "ns.example.com.", EXAMPLE_NS),
        "loop-b.test.": _delegate("test.", "ns.example.com.", EXAMPLE_NS),
    },

    NET_TLD: {
        "shop.fastcdn.net.": _delegate("fastcdn.net.", "ns.fastcdn.net.", FASTCDN_NS),
        "cdn.fastcdn.net.":  _delegate("fastcdn.net.", "ns.fastcdn.net.", FASTCDN_NS),
    },

    ANTHROPIC_NS: {
        "anthropic.com.": _answer_a("anthropic.com.", "160.79.104.10"),
    },

    API_ANTHROPIC_NS: {
        "api.anthropic.com.": _answer_a("api.anthropic.com.", "104.16.1.1"),
    },

    CLOUDFLARE_NS: {
        "gemma.ns.cloudflare.com.": _answer_a("gemma.ns.cloudflare.com.", API_ANTHROPIC_NS),
        "ns.cloudflare.com.":       _answer_a("ns.cloudflare.com.", CLOUDFLARE_NS),
    },

    EXAMPLE_NS: {
        # CNAME chain: www -> example -> A
        "www.example.com.":   _answer_cname("www.example.com.", "example.com."),
        "example.com.":       _answer_a("example.com.", "93.184.216.34"),
        # Multi-hop CNAME: store -> shop.fastcdn (cross-TLD)
        "store.example.com.": _answer_cname("store.example.com.", "shop.fastcdn.net."),
        # CNAME loop
        "loop-a.test.": _answer_cname("loop-a.test.", "loop-b.test."),
        "loop-b.test.": _answer_cname("loop-b.test.", "loop-a.test."),
    },

    FASTCDN_NS: {
        # Continue multi-hop CNAME: shop -> cdn -> A
        "shop.fastcdn.net.": _answer_cname("shop.fastcdn.net.", "cdn.fastcdn.net."),
        "cdn.fastcdn.net.":  _answer_a("cdn.fastcdn.net.", "203.0.113.99"),
    },

    DEAD_NS: {
        # All queries return REFUSED (this server is decommissioned).
    },
    DEADNS_BACKUP: {
        "deadns.com.": _answer_a("deadns.com.", "192.0.2.99"),
    },
}


# ─────── Call-counter / call-log state (for tests to reset/inspect) ───────
_state_lock = threading.Lock()
_query_count = 0
_call_log: "list[tuple[str, str]]" = []
_in_flight = 0
_peak_in_flight = 0
_in_flight_hold = 0.0       # tests set this > 0 to force overlap


def reset_call_counter() -> None:
    """Tests call this in setUp to start each test with a fresh counter + log."""
    global _query_count, _in_flight, _peak_in_flight, _in_flight_hold
    with _state_lock:
        _query_count = 0
        _in_flight = 0
        _peak_in_flight = 0
        _in_flight_hold = 0.0
        _call_log.clear()


def get_call_count() -> int:
    return _query_count


def get_call_log() -> "list[tuple[str, str]]":
    """Return the (name, server_ip) sequence since the last reset."""
    with _state_lock:
        return list(_call_log)


def get_peak_in_flight() -> int:
    """Maximum number of concurrent send_query calls observed."""
    return _peak_in_flight


def set_in_flight_hold(seconds: float) -> None:
    """Make every send_query sleep this long inside the in-flight region.
    Used by Step 7 tests to force overlap between concurrent resolves."""
    global _in_flight_hold
    _in_flight_hold = seconds


# ─────── The user-facing API ───────
def send_query(normalized_name: str, server_ip: str) -> DNSResponse:
    """Simulate the network call to (server_ip, port 53) for normalized_name.

    Args:
        normalized_name: Fully-qualified domain name to look up (e.g.
            "example.com."). Must be lowercase with trailing dot —
            normalize first.
        server_ip: IPv4 address of the DNS server to query.

    Returns:
        A DNSResponse whose status is one of:
        - "NOERROR" — the server handled the query. Check answer
          (direct results), authority (delegations), and additional
          (glue) to decide what to do next.
        - "NXDOMAIN" — the name does not exist in this server's zone.
        - "REFUSED" — the server has no zone covering this name
          (you asked the wrong server).

    Raises:
        TypeError: if either argument is not a str.
        ValueError: if the strings don't look like a normalized name / IP.
        QueryLimitExceeded: if send_query has been called more than
            QUERY_LIMIT times since the counter was last reset — almost
            certainly means an infinite loop in the resolver.
    """
    # Argument validation — catch swapped or wrong-type args.
    if not isinstance(normalized_name, str) or not isinstance(server_ip, str):
        raise TypeError(
            f"send_query(name, server_ip) expects two strings, got "
            f"({type(normalized_name).__name__}, {type(server_ip).__name__})"
        )
    if not _looks_like_normalized(normalized_name):
        raise ValueError(
            f"send_query(name, server_ip): first argument should "
            f"be a domain name, not an IP address: {normalized_name!r}"
        )
    if not _looks_like_ip(server_ip):
        raise ValueError(
            f"send_query(name, server_ip): second argument should "
            f"be an IP address, but got: {server_ip!r}"
        )

    global _query_count, _in_flight, _peak_in_flight
    with _state_lock:
        _query_count += 1
        if _query_count > QUERY_LIMIT:
            raise QueryLimitExceeded(
                f"send_query called {_query_count} times (limit: {QUERY_LIMIT}). "
                "Your resolver likely has an infinite loop or is not respecting max_queries."
            )
        _call_log.append((normalized_name, server_ip))
        _in_flight += 1
        if _in_flight > _peak_in_flight:
            _peak_in_flight = _in_flight
        hold = _in_flight_hold

    try:
        if hold > 0:
            time.sleep(hold)
        server_table = ZONES.get(server_ip, {})
        return server_table.get(normalized_name, _REFUSED)
    finally:
        with _state_lock:
            _in_flight -= 1
