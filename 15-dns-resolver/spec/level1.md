# Level 1 — Basic delegation (root → TLD → authoritative)

## What you're building

You're writing a recursive DNS resolver in pure Python. Given a domain name like `Anthropic.COM`, you walk down from the root server (`ROOT_SERVER`) following NS delegations until some server gives you a direct `A` answer record, and you return its `rdata` (the IP).

For Level 1 we keep it as simple as possible:

- Every response has `status='NOERROR'`.
- Each `authority` list has **exactly one** `NS` record.
- The matching glue (`A` record) for that NS is **always** in the same response's `additional` section.
- Direct answers, when they come, are always type `A` (no `CNAME` until Level 2).

## Two functions to implement

```python
def normalize(name: str) -> str:
    """Lowercase + ensure trailing dot. 'Anthropic.COM' -> 'anthropic.com.'"""

def resolve(domain_name: str, max_queries: int = 15) -> str | None:
    """Recursively resolve domain_name to an IP, starting at ROOT_SERVER.

    Returns the IP string, or None if it can't be resolved.
    max_queries is unused until Level 5.
    """
```

## The annotated walk-through

Suppose you call `resolve("Anthropic.COM")`. After normalizing to `"anthropic.com."`, you start at `ROOT_SERVER`:

```
send_query("anthropic.com.", ROOT_SERVER) →
  DNSResponse(
      status='NOERROR',
      answer=None,
      authority=[DNSRecord(name='com.', rdtype='NS', rdata='a.gtld-servers.net.')],
      additional=[DNSRecord(name='a.gtld-servers.net.', rdtype='A',    rdata='192.5.6.30'),
                  DNSRecord(name='a.gtld-servers.net.', rdtype='AAAA', rdata='2001:db8::1')],
  )
```

Root says "I don't know, ask `a.gtld-servers.net.` which is at `192.5.6.30`". The IPv4 glue is the `A` record in `additional` — **ignore the `AAAA` IPv6 record**. So the next step:

```
send_query("anthropic.com.", "192.5.6.30") →
  DNSResponse(
      status='NOERROR', answer=None,
      authority=[DNSRecord(name='anthropic.com.', rdtype='NS', rdata='isla.ns.cloudflare.com.')],
      additional=[DNSRecord(name='isla.ns.cloudflare.com.', rdtype='A', rdata='108.162.192.119')],
  )
```

TLD delegates to Cloudflare. Continue:

```
send_query("anthropic.com.", "108.162.192.119") →
  DNSResponse(
      status='NOERROR',
      answer=DNSRecord(name='anthropic.com.', rdtype='A', rdata='160.79.104.10'),
      authority=[], additional=[],
  )
```

Got an `A` answer. Return `'160.79.104.10'`.

## The algorithm

```
next_server = ROOT_SERVER
while True:
    response = send_query(normalized_name, next_server)
    if response.answer is not None and response.answer.rdtype == 'A':
        return response.answer.rdata
    # Find the (one) glue A record in additional and use it as the next server.
    ns_name = response.authority[0].rdata
    next_server = the rdata of the additional record where rdtype=='A' and name==ns_name
```

## Provided helpers

- `from dns_mock import send_query, ROOT_SERVER, install_scenario`
- `from dns_types import DNSResponse, DNSRecord`

`send_query` raises `ValueError` if you pass a name that isn't lowercase with a trailing dot, so `normalize()` first.

## Don't worry about (yet)

- `CNAME` answers — Level 2
- Empty `additional` — Level 3
- `NXDOMAIN` / `REFUSED` — Level 4
- Cycles or infinite loops — Level 5
- Multiple domains — Level 6
- Concurrency — Level 7

If a test gives you `status='NOERROR'` and you get stuck, just assume the spec for this level holds (one NS, one matching glue, A answer eventually).

## Run

```bash
python3 test_level1.py
```
