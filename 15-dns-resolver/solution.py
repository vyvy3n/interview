"""Reference DNS resolver — Levels 1 through 7.

Single recursive engine, factored so the send_query call point is a parameter.
That makes Level 6 (caching) and Level 7 (bounded concurrency) trivial wrappers
on top of the Level 1-5 logic.
"""
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable

from dns_mock import ROOT_SERVER, send_query
from dns_types import DNSRecord, DNSResponse


# ---------- Level 1: normalize ----------

def normalize(name: str) -> str:
    """Lowercase + ensure trailing dot. 'Anthropic.COM' -> 'anthropic.com.'"""
    n = name.lower()
    return n if n.endswith(".") else n + "."


# ---------- Levels 1-5: single-domain resolve ----------

class _GiveUp(Exception):
    """Raised internally when max_queries is exhausted — caught at top level."""


# Sentinel for "this server refused, try the next NS at the parent level."
# None means "give up — name doesn't exist or all options exhausted."
_REFUSED = object()


def _glue_ip_for(ns_name: str, additional: list) -> str | None:
    """Return the IPv4 glue address for ns_name, or None if not present."""
    for record in additional:
        if record.rdtype == "A" and record.name == ns_name:
            return record.rdata
    return None


def _resolve(name: str, query_fn: Callable, state: dict) -> str | None:
    """Resolve `name` (already normalized), starting from ROOT_SERVER.

    query_fn(name, server_ip) -> DNSResponse — abstracted so Level 6/7 can
    inject a cached / semaphore-bounded version.
    state: {"queries": int, "limit": int} shared across the entire top-level
    resolve so cycle detection works across CNAME/NS recursion.
    """
    current = name
    while True:
        answer = _walk_from(current, ROOT_SERVER, query_fn, state)
        if answer is None or answer is _REFUSED:
            return None
        if answer.rdtype == "A":
            return answer.rdata
        # CNAME → restart from root with the alias
        current = answer.rdata


def _walk_from(name: str, server: str, query_fn: Callable, state: dict):
    """Recursively walk one delegation from `server` for `name`.

    Returns DNSRecord (A or CNAME answer), None (give up — NXDOMAIN or all
    NS fallbacks exhausted), or _REFUSED sentinel (caller should try next NS).
    """
    response = _query(query_fn, name, server, state)
    if response.status == "NXDOMAIN":
        return None
    if response.status == "REFUSED":
        return _REFUSED
    # NOERROR
    if response.answer is not None:
        return response.answer
    # Delegated. Try each NS in order; if a sub-walk REFUSES, fall back to next.
    for ns_record in response.authority:
        if ns_record.rdtype != "NS":
            continue
        ns_name = ns_record.rdata
        glue = _glue_ip_for(ns_name, response.additional)
        if glue is not None:
            next_server = glue
        else:
            ns_ip = _resolve(ns_name, query_fn, state)
            if ns_ip is None:
                continue   # can't reach this NS, try the next one
            next_server = ns_ip
        result = _walk_from(name, next_server, query_fn, state)
        if result is _REFUSED:
            continue          # try next NS at this level
        return result         # NXDOMAIN (None) or answer (DNSRecord)
    return None               # exhausted every NS


def _query(query_fn: Callable, name: str, server: str, state: dict) -> DNSResponse:
    """Wrapped send_query that enforces the global max_queries cap."""
    if state["queries"] >= state["limit"]:
        raise _GiveUp
    state["queries"] += 1
    return query_fn(name, server)


def resolve(domain_name: str, max_queries: int = 15) -> "str | None":
    """Resolve a domain name to an IPv4 address, or None.

    Raises nothing user-visible — internal _GiveUp is caught here.
    """
    state = {"queries": 0, "limit": max_queries}
    try:
        return _resolve(normalize(domain_name), send_query, state)
    except _GiveUp:
        return None


# ---------- Levels 6-7: batch resolution ----------

def resolve_all(
    domains: list,
    max_workers: int = 5,
    max_queries: int = 15,
) -> dict:
    """Resolve every domain in `domains`, return {input_domain: ip_or_None}.

    Implements the Step 6 + Step 7 requirements:
      - Cache (name, server) -> DNSResponse, scoped to this call.
      - NXDOMAIN and REFUSED responses are cached just like NOERROR.
      - max_queries is per-domain. A cache hit does not call send_query but
        still counts against that domain's budget (handled by _query).
      - At most max_workers send_query calls in flight at any time (Semaphore).
      - If a (name, server) query is already in flight, wait for it rather
        than sending a duplicate (Future-based single-flight dedup).
      - Result keys preserve the original input form.
    """
    cache: dict = {}
    in_flight: dict = {}            # (name, server) -> Future[DNSResponse]
    state_lock = threading.Lock()
    semaphore = threading.Semaphore(max_workers)

    def cached_send_query(name: str, server_ip: str) -> DNSResponse:
        key = (name, server_ip)
        # Phase 1: under the lock, decide whether to be the runner, the waiter,
        # or a cache reader — without doing any I/O.
        with state_lock:
            if key in cache:
                return cache[key]
            existing = in_flight.get(key)
            if existing is not None:
                future = existing
                we_run = False
            else:
                future = Future()
                in_flight[key] = future
                we_run = True

        # Phase 2: waiters block on the runner's Future. Releases the lock
        # so the runner can acquire it later to publish the result.
        if not we_run:
            return future.result()

        # Phase 3: we're the runner — bound concurrency, then call send_query.
        try:
            with semaphore:
                response = send_query(name, server_ip)
        except BaseException as exc:
            with state_lock:
                in_flight.pop(key, None)
            future.set_exception(exc)
            raise

        with state_lock:
            cache[key] = response
            in_flight.pop(key, None)
        future.set_result(response)
        return response

    def resolve_one(input_domain: str) -> "str | None":
        state = {"queries": 0, "limit": max_queries}
        try:
            return _resolve(normalize(input_domain), cached_send_query, state)
        except _GiveUp:
            return None

    if not domains:
        return {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_for = {d: pool.submit(resolve_one, d) for d in domains}
        return {d: f.result() for d, f in future_for.items()}
