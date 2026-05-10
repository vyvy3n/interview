# Level 3 — Missing glue records

## New behavior

Sometimes a server delegates to a nameserver but **doesn't include the nameserver's IP** in `additional`:

```
send_query("api.anthropic.com.", server) →
  DNSResponse(
      status='NOERROR', answer=None,
      authority=[DNSRecord(name='api.anthropic.com.', rdtype='NS', rdata='gemma.ns.cloudflare.com.')],
      additional=[],   # no glue!
  )
```

You can't query `gemma.ns.cloudflare.com.` directly — that's a name, not an IP. So you must **resolve the nameserver's name first, starting from the root**, then continue resolving the original name with the IP you just looked up.

## The recursive shape

```python
# inside your delegation walk, when you need to follow the NS:
ns_name = authority[0].rdata
glue = first A record in additional where name == ns_name, else None
if glue is not None:
    next_server = glue.rdata
else:
    next_server = resolve(ns_name)   # recursively resolve the NS
    if next_server is None:
        return None                   # can't continue
```

Yes, you call your own `resolve()` recursively. That's expected.

## Stay assuming

- Still `status='NOERROR'` only.
- Still exactly one `NS` per `authority`.

## Don't worry about

- Multiple NS records — Level 4.
- Cycles in glue lookups (zone A's NS lives in zone B and vice versa) — Level 5.

## Run

```bash
python3 test_level3.py
```
