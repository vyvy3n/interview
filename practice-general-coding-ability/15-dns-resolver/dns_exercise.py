"""Starter file — replicates the assessment's dns_exercise.py.

This is what the assessment hands you. You fill in the TODO blocks.
For the worked-out reference, see solution.py.
"""
from dns_mock import send_query, ROOT_SERVER
from dns_types import DNSRecord, DNSResponse, ServerIP


def normalize(name: str) -> str:
    """Normalize a DNS name to lowercased form with a trailing dot.

    >>> normalize("anthropic.com.")
    'anthropic.com.'
    >>> normalize("Docs.Anthropic.Com")
    'docs.anthropic.com.'
    >>> normalize("ANTHROPIC.COM")
    'anthropic.com.'
    """
    # TODO: STEP 0: YOUR CODE HERE
    return name


def resolve(
    domain_name: str,
    max_queries: int = 15,
) -> "ServerIP | None":
    """Resolve a domain name to an IP address.

    Start by querying ROOT_SERVER and follow delegations
    until you get an answer.

    Returns an IP address, or None if the domain can't
    be resolved.

    Starting at Step 5, gives up after max_queries
    calls to send_query to prevent infinite loops.
    """
    # TODO: STEP 1: YOUR CODE HERE
    return None


def resolve_all(
    domains: list,
    max_workers: int = 5,
    max_queries: int = 15,
) -> dict:
    """Resolve all domains, caching calls to send_query.

    The cache must be scoped to this call (not global) so
    that each invocation of resolve_all() starts fresh.

    Starting at Step 7, at most max_workers calls to
    send_query may be in flight at any time.
    """
    # TODO: STEP 6: YOUR CODE HERE
    return {}
