"""Independent solution to the DNS resolver problem.

Written from the spec only — does not look at solution.py.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, Future

from dns_mock import send_query, ROOT_SERVER
from dns_types import DNSResponse, ServerIP


# ─────────────────────────────────────────────────────────────────────────────
# Step 0 — normalize
# ─────────────────────────────────────────────────────────────────────────────
def normalize(name: str) -> str:
    """Lowercase and ensure a trailing dot."""
    name = name.lower()
    if not name.endswith("."):
        name += "."
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Internal resolver — works against an injectable "query" callable so that
# resolve_all() can swap in a caching/single-flight version.
# ─────────────────────────────────────────────────────────────────────────────
class _QueryBudget:
    """Tracks remaining query budget for a single resolve() call.

    Counts both real send_query calls AND cache hits (per spec for Step 6:
    "A cache hit does not call send_query, but still counts against the limit").
    """

    def __init__(self, max_queries: int):
        self.remaining = max_queries

    def spend(self) -> bool:
        """Try to spend one unit. Returns True if budget remained."""
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        return True


def _glue_ip(name: str, additional: list) -> "ServerIP | None":
    """Find the first A-record in additional whose name matches."""
    for rec in additional:
        if rec.name == name and rec.rdtype == "A":
            return rec.rdata
    return None


def _resolve_from(
    current_name: str,
    server_ip: ServerIP,
    budget: _QueryBudget,
    query_fn,
    cname_chain: set,
) -> "ServerIP | None":
    """Resolve current_name starting by querying server_ip.

    Returns the IP, or None on failure (NXDOMAIN, REFUSED at this server,
    or budget exhausted, or all delegation children fail).
    """
    if not budget.spend():
        return None
    try:
        response: DNSResponse = query_fn(current_name, server_ip)
    except Exception:
        return None

    if response.status == "NXDOMAIN":
        # Definitively does not exist — propagate as None (and signal
        # to the caller that there's no point trying siblings, but our
        # simple model just returns None).
        return None
    if response.status == "REFUSED":
        # Caller handles fallback to the next NS sibling.
        return None

    # NOERROR
    ans = response.answer
    if ans is not None:
        if ans.rdtype == "A":
            return ans.rdata
        if ans.rdtype == "CNAME":
            alias = ans.rdata
            if alias in cname_chain:
                return None
            cname_chain.add(alias)
            # Restart from root with the new name.
            return _resolve_from(
                alias, ROOT_SERVER, budget, query_fn, cname_chain
            )
        return None

    # Delegation — walk NS records in order.
    for ns_record in response.authority:
        if ns_record.rdtype != "NS":
            continue
        ns_name = ns_record.rdata
        glue = _glue_ip(ns_name, response.additional)
        if glue is None:
            # Need to resolve the NS name first.
            ns_ip = _resolve_from(
                ns_name, ROOT_SERVER, budget, query_fn, set()
            )
            if ns_ip is None:
                continue
        else:
            ns_ip = glue
        # Try following this delegation. If it fails (REFUSED, missing
        # glue chain dead end, …), fall through to the next NS.
        result = _resolve_from(
            current_name, ns_ip, budget, query_fn, cname_chain
        )
        if result is not None:
            return result
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Step 1–5 — resolve()
# ─────────────────────────────────────────────────────────────────────────────
def resolve(domain_name: str, max_queries: int = 15) -> "ServerIP | None":
    name = normalize(domain_name)
    budget = _QueryBudget(max_queries)
    return _resolve_from(name, ROOT_SERVER, budget, send_query, set())


# ─────────────────────────────────────────────────────────────────────────────
# Step 6 + 7 — resolve_all() with caching, single-flight, bounded concurrency
# ─────────────────────────────────────────────────────────────────────────────
def resolve_all(
    domains: list,
    max_workers: int = 5,
    max_queries: int = 15,
) -> dict:
    """Resolve all domains concurrently with a per-call cache.

    - Cache: (name, server_ip) -> DNSResponse. NXDOMAIN/REFUSED cached too.
    - Cache hits don't call send_query but still count against per-domain
      max_queries.
    - At most max_workers send_query calls in flight at once.
    - In-flight queries are de-duplicated: a second domain wanting the same
      (name, server_ip) waits for the first one's result.
    """
    cache: dict = {}                # (name, server_ip) -> DNSResponse
    in_flight: dict = {}            # (name, server_ip) -> Future[DNSResponse]
    cache_lock = threading.Lock()

    # Bounded concurrency: a semaphore limits concurrent send_query calls.
    # We use this rather than the executor's worker count because a worker
    # may be blocked waiting for an in-flight query (which doesn't count
    # against the in-flight budget for *this* worker).
    sem = threading.Semaphore(max_workers)

    def cached_query(name: str, server_ip: ServerIP) -> DNSResponse:
        key = (name, server_ip)
        with cache_lock:
            if key in cache:
                return cache[key]
            fut = in_flight.get(key)
            if fut is None:
                # We are the first to request this — register a Future
                # and do the work ourselves (outside the lock).
                fut = Future()
                in_flight[key] = fut
                owner = True
            else:
                owner = False

        if owner:
            try:
                with sem:
                    result = send_query(name, server_ip)
                with cache_lock:
                    cache[key] = result
                    in_flight.pop(key, None)
                fut.set_result(result)
                return result
            except BaseException as exc:
                with cache_lock:
                    in_flight.pop(key, None)
                fut.set_exception(exc)
                raise
        else:
            # Wait for the in-flight result. This does NOT consume a
            # send_query slot — we're just blocked on someone else's
            # send_query.
            return fut.result()

    def resolve_one(domain: str) -> "ServerIP | None":
        name = normalize(domain)
        budget = _QueryBudget(max_queries)
        return _resolve_from(name, ROOT_SERVER, budget, cached_query, set())

    results: dict = {}

    if not domains:
        return results

    # Use a thread pool for per-domain parallelism. The semaphore inside
    # cached_query is what bounds *send_query* concurrency; we let the
    # pool be as wide as needed for resolves to make progress (a resolve
    # waiting on someone else's in-flight should not occupy a send_query
    # slot).
    pool_size = max(max_workers, len(domains))
    with ThreadPoolExecutor(max_workers=pool_size) as ex:
        future_to_domain = {
            ex.submit(resolve_one, d): d for d in domains
        }
        for fut in future_to_domain:
            d = future_to_domain[fut]
            try:
                results[d] = fut.result()
            except Exception:
                results[d] = None

    return results
