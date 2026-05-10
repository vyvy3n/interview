"""Mock DNS server — replicates the assessment-provided send_query behavior.

A scenario is a dict { server_ip: { normalized_name: DNSResponse } }. Anything
not in the dict returns NOERROR with empty sections (treated as 'I don't know').

Validates inputs and tracks query count to catch infinite loops, just like the
real mock used in the test.
"""
import re
import threading
from typing import Callable

from dns_types import DNSResponse


ROOT_SERVER = "198.41.0.4"   # a.root-servers.net.
QUERY_LIMIT = 500


class _State:
    """Process-wide mock state (shared across all worker threads)."""

    def __init__(self):
        self.scenario: dict = {}
        self.count: int = 0
        self.limit: int = QUERY_LIMIT
        self.observer: "Callable | None" = None
        self.lock = threading.Lock()


_state = _State()


def _looks_like_ip(s: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", s))


def _looks_like_normalized(s: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9.\-]+\.", s))


class QueryLimitExceeded(RuntimeError):
    """Raised when too many send_query calls happen — likely an infinite loop."""


def install_scenario(scenario: dict, limit: int = QUERY_LIMIT, observer: "Callable | None" = None) -> None:
    """Install the DNS topology a test should answer from. Resets the counter.

    observer: optional callback (name, server_ip) -> None invoked on every
    send_query, so tests can assert on call sequence and concurrency.
    """
    with _state.lock:
        _state.scenario = scenario
        _state.count = 0
        _state.limit = limit
        _state.observer = observer


def reset() -> None:
    install_scenario({})


def query_count() -> int:
    return _state.count


def send_query(normalized_name: str, server_ip: str) -> DNSResponse:
    """Mock the network call to (server_ip, port 53) for normalized_name.

    normalized_name: must be lowercase with trailing dot — normalize first.
    server_ip: IPv4 address of the DNS server to query.

    Raises:
        TypeError if either argument is not a str.
        ValueError if the strings don't look like a normalized name / IP.
        QueryLimitExceeded if you've called send_query > limit times in this
        scenario — almost certainly means a cycle in your resolver.
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

    with _state.lock:
        _state.count += 1
        if _state.count > _state.limit:
            raise QueryLimitExceeded(
                f"send_query called {_state.count} times (limit: {_state.limit}). "
                "Your resolver likely has an infinite loop or is not respecting max_queries."
            )
        observer = _state.observer
        scenario = _state.scenario

    if observer is not None:
        observer(normalized_name, server_ip)

    server_table = scenario.get(server_ip, {})
    return server_table.get(
        normalized_name,
        # Default: server has no idea. Treat unknown queries as REFUSED so
        # tests can distinguish 'wrong server' from 'no such name'.
        DNSResponse(status="REFUSED", answer=None, authority=[], additional=[]),
    )
