"""Shared DNS scenario fixtures used across test files."""
from dns_mock import ROOT_SERVER
from dns_types import DNSRecord, DNSResponse


# ---- Server IPs (made-up but topologically consistent) ----
COM_TLD = "192.5.6.30"
NET_TLD = "192.5.6.31"
CF_AUTH = "108.162.192.119"            # isla.ns.cloudflare.com.
CF_AUTH_2 = "108.162.192.120"          # gemma.ns.cloudflare.com.
EXAMPLE_AUTH = "93.184.216.34"
DEAD_NS_1 = "192.0.2.1"
DEAD_NS_2 = "192.0.2.2"


def _resp(answer=None, authority=None, additional=None, status="NOERROR"):
    return DNSResponse(
        status=status,
        answer=answer,
        authority=authority or [],
        additional=additional or [],
    )


def _ns(zone, ns_name):
    return DNSRecord(name=zone, rdtype="NS", rdata=ns_name)


def _a(name, ip):
    return DNSRecord(name=name, rdtype="A", rdata=ip)


def _cname(name, alias):
    return DNSRecord(name=name, rdtype="CNAME", rdata=alias)


# ---- Level 1: anthropic.com → 160.79.104.10 (single NS, glue present) ----
SCENARIO_BASIC = {
    ROOT_SERVER: {
        "anthropic.com.": _resp(
            authority=[_ns("com.", "a.gtld-servers.net.")],
            additional=[_a("a.gtld-servers.net.", COM_TLD)],
        ),
    },
    COM_TLD: {
        "anthropic.com.": _resp(
            authority=[_ns("anthropic.com.", "isla.ns.cloudflare.com.")],
            additional=[_a("isla.ns.cloudflare.com.", CF_AUTH)],
        ),
    },
    CF_AUTH: {
        "anthropic.com.": _resp(answer=_a("anthropic.com.", "160.79.104.10")),
    },
}


# ---- Level 2: CNAME single-hop and multi-hop ----
SCENARIO_CNAME_SINGLE = {
    ROOT_SERVER: {
        "www.example.com.": _resp(
            authority=[_ns("com.", "a.gtld-servers.net.")],
            additional=[_a("a.gtld-servers.net.", COM_TLD)],
        ),
        "example.com.": _resp(
            authority=[_ns("com.", "a.gtld-servers.net.")],
            additional=[_a("a.gtld-servers.net.", COM_TLD)],
        ),
    },
    COM_TLD: {
        "www.example.com.": _resp(
            authority=[_ns("example.com.", "ns.example.com.")],
            additional=[_a("ns.example.com.", EXAMPLE_AUTH)],
        ),
        "example.com.": _resp(
            authority=[_ns("example.com.", "ns.example.com.")],
            additional=[_a("ns.example.com.", EXAMPLE_AUTH)],
        ),
    },
    EXAMPLE_AUTH: {
        "www.example.com.": _resp(answer=_cname("www.example.com.", "example.com.")),
        "example.com.": _resp(answer=_a("example.com.", "93.184.216.34")),
    },
}


SCENARIO_CNAME_MULTIHOP = {
    ROOT_SERVER: {
        "store.example.com.": _resp(
            authority=[_ns("com.", "a.gtld-servers.net.")],
            additional=[_a("a.gtld-servers.net.", COM_TLD)],
        ),
        "shop.fastcdn.net.": _resp(
            authority=[_ns("net.", "a.gtld-servers.net.")],
            additional=[_a("a.gtld-servers.net.", NET_TLD)],
        ),
        "cdn.fastcdn.net.": _resp(
            authority=[_ns("net.", "a.gtld-servers.net.")],
            additional=[_a("a.gtld-servers.net.", NET_TLD)],
        ),
    },
    COM_TLD: {
        "store.example.com.": _resp(
            authority=[_ns("example.com.", "ns.example.com.")],
            additional=[_a("ns.example.com.", EXAMPLE_AUTH)],
        ),
    },
    NET_TLD: {
        "shop.fastcdn.net.": _resp(
            authority=[_ns("fastcdn.net.", "ns.fastcdn.net.")],
            additional=[_a("ns.fastcdn.net.", "203.0.113.5")],
        ),
        "cdn.fastcdn.net.": _resp(
            authority=[_ns("fastcdn.net.", "ns.fastcdn.net.")],
            additional=[_a("ns.fastcdn.net.", "203.0.113.5")],
        ),
    },
    EXAMPLE_AUTH: {
        "store.example.com.": _resp(answer=_cname("store.example.com.", "shop.fastcdn.net.")),
    },
    "203.0.113.5": {
        "shop.fastcdn.net.": _resp(answer=_cname("shop.fastcdn.net.", "cdn.fastcdn.net.")),
        "cdn.fastcdn.net.": _resp(answer=_a("cdn.fastcdn.net.", "203.0.113.99")),
    },
}


# ---- Level 3: missing glue, recursive NS-name lookup ----
def scenario_missing_glue():
    """api.anthropic.com → NS gemma.ns.cloudflare.com (no glue) → recursive resolve → A."""
    return {
        ROOT_SERVER: {
            "api.anthropic.com.": _resp(
                authority=[_ns("com.", "a.gtld-servers.net.")],
                additional=[_a("a.gtld-servers.net.", COM_TLD)],
            ),
            "gemma.ns.cloudflare.com.": _resp(
                authority=[_ns("com.", "a.gtld-servers.net.")],
                additional=[_a("a.gtld-servers.net.", COM_TLD)],
            ),
        },
        COM_TLD: {
            "api.anthropic.com.": _resp(
                authority=[_ns("api.anthropic.com.", "gemma.ns.cloudflare.com.")],
                additional=[],   # no glue!
            ),
            "gemma.ns.cloudflare.com.": _resp(
                authority=[_ns("cloudflare.com.", "ns.cloudflare.com.")],
                additional=[_a("ns.cloudflare.com.", "162.159.0.33")],
            ),
        },
        "162.159.0.33": {
            "gemma.ns.cloudflare.com.": _resp(answer=_a("gemma.ns.cloudflare.com.", CF_AUTH_2)),
        },
        CF_AUTH_2: {
            "api.anthropic.com.": _resp(answer=_a("api.anthropic.com.", "104.16.1.1")),
        },
    }


# ---- Level 4: NS fallback + statuses ----
def scenario_ns_fallback_refused():
    """First NS REFUSES, second NS succeeds."""
    return {
        ROOT_SERVER: {
            "deadns.com.": _resp(
                authority=[_ns("com.", "a.gtld-servers.net.")],
                additional=[_a("a.gtld-servers.net.", COM_TLD)],
            ),
        },
        COM_TLD: {
            "deadns.com.": _resp(
                authority=[
                    _ns("deadns.com.", "ns1.deadns.com."),
                    _ns("deadns.com.", "ns2.deadns.com."),
                ],
                additional=[
                    _a("ns1.deadns.com.", DEAD_NS_1),
                    _a("ns2.deadns.com.", DEAD_NS_2),
                ],
            ),
        },
        DEAD_NS_1: {
            # Returns REFUSED — nothing in this dict, mock default is REFUSED.
        },
        DEAD_NS_2: {
            "deadns.com.": _resp(answer=_a("deadns.com.", "192.0.2.99")),
        },
    }


def scenario_ns_fallback_no_glue():
    """First NS has no glue and resolving its name fails; second NS succeeds."""
    return {
        ROOT_SERVER: {
            "split.com.": _resp(
                authority=[_ns("com.", "a.gtld-servers.net.")],
                additional=[_a("a.gtld-servers.net.", COM_TLD)],
            ),
            "phantom.example.": _resp(
                # phantom.example. doesn't exist anywhere → recursive resolve fails
                status="NXDOMAIN", answer=None,
            ),
        },
        COM_TLD: {
            "split.com.": _resp(
                authority=[
                    _ns("split.com.", "phantom.example."),
                    _ns("split.com.", "ns2.deadns.com."),
                ],
                additional=[_a("ns2.deadns.com.", DEAD_NS_2)],
            ),
        },
        DEAD_NS_2: {
            "split.com.": _resp(answer=_a("split.com.", "192.0.2.42")),
        },
    }


def scenario_nxdomain():
    return {
        ROOT_SERVER: {
            "missing.example.": _resp(status="NXDOMAIN", answer=None),
        },
    }


def scenario_all_ns_fail():
    return {
        ROOT_SERVER: {
            "broken.com.": _resp(
                authority=[_ns("com.", "a.gtld-servers.net.")],
                additional=[_a("a.gtld-servers.net.", COM_TLD)],
            ),
        },
        COM_TLD: {
            "broken.com.": _resp(
                authority=[
                    _ns("broken.com.", "ns1.broken.com."),
                    _ns("broken.com.", "ns2.broken.com."),
                ],
                additional=[
                    _a("ns1.broken.com.", DEAD_NS_1),
                    _a("ns2.broken.com.", "192.0.2.3"),
                ],
            ),
        },
        # Both NS IPs return REFUSED (default) — every fallback fails.
    }


# ---- Level 5: cycles ----
def scenario_cname_loop():
    """A → B → A — should be killed by max_queries."""
    return {
        ROOT_SERVER: {
            "a.example.": _resp(
                authority=[_ns("example.", "ns.example.")],
                additional=[_a("ns.example.", "203.0.113.10")],
            ),
            "b.example.": _resp(
                authority=[_ns("example.", "ns.example.")],
                additional=[_a("ns.example.", "203.0.113.10")],
            ),
        },
        "203.0.113.10": {
            "a.example.": _resp(answer=_cname("a.example.", "b.example.")),
            "b.example.": _resp(answer=_cname("b.example.", "a.example.")),
        },
    }


def scenario_glue_cycle():
    """zone-A's NS lives in zone-B, zone-B's NS lives in zone-A."""
    return {
        ROOT_SERVER: {
            "x.alpha.": _resp(
                authority=[_ns("alpha.", "ns.beta.")],
                additional=[],   # no glue, must resolve ns.beta.
            ),
            "ns.beta.": _resp(
                authority=[_ns("beta.", "ns.alpha.")],
                additional=[],   # no glue, must resolve ns.alpha.
            ),
            "ns.alpha.": _resp(
                authority=[_ns("alpha.", "ns.beta.")],
                additional=[],   # cycle!
            ),
        },
    }


# ---- Level 6/7: batch resolution scenarios ----
def scenario_batch_overlap():
    """Three subdomains of example.com sharing the .com TLD + example.com auth chain."""
    return {
        ROOT_SERVER: {
            n: _resp(
                authority=[_ns("com.", "a.gtld-servers.net.")],
                additional=[_a("a.gtld-servers.net.", COM_TLD)],
            )
            for n in ("www.example.com.", "api.example.com.", "cdn.example.com.")
        },
        COM_TLD: {
            n: _resp(
                authority=[_ns("example.com.", "ns.example.com.")],
                additional=[_a("ns.example.com.", EXAMPLE_AUTH)],
            )
            for n in ("www.example.com.", "api.example.com.", "cdn.example.com.")
        },
        EXAMPLE_AUTH: {
            "www.example.com.": _resp(answer=_a("www.example.com.", "93.184.216.1")),
            "api.example.com.": _resp(answer=_a("api.example.com.", "93.184.216.2")),
            "cdn.example.com.": _resp(answer=_a("cdn.example.com.", "93.184.216.3")),
        },
    }
