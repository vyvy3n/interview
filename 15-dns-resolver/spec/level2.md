# Level 2 — CNAME records

## New behavior

Some servers, instead of returning an `A` answer, return a `CNAME` answer:

```
send_query("www.example.com.", server) →
  DNSResponse(
      status='NOERROR',
      answer=DNSRecord(name='www.example.com.', rdtype='CNAME', rdata='example.com.'),
      authority=[], additional=[],
  )
```

A `CNAME` is an alias. To finish the resolution, **start the entire process over from the root server**, but using the alias name (`example.com.`) instead of the original (`www.example.com.`).

Chains can be multi-hop: `store.example.com.` may CNAME to `shop.fastcdn.net.`, which CNAMEs to `cdn.fastcdn.net.`, which finally has an `A` record.

## What changes

Wrap your Level 1 walk in an outer loop that handles the CNAME-restart case. A clean shape:

```python
current = normalize(domain_name)
while True:
    answer = walk_from_root(current)   # your Level 1 logic, returning the answer record (not just rdata)
    if answer is None:
        return None
    if answer.rdtype == 'A':
        return answer.rdata
    if answer.rdtype == 'CNAME':
        current = answer.rdata          # restart from root with the new name
```

## Stay assuming

- Every response is `status='NOERROR'`.
- Each `authority` has exactly one NS, with matching glue in `additional`.

## Don't worry about

- Cycles in CNAME chains (e.g. A → B → A) — Level 5 catches this via `max_queries`.

## Run

```bash
python3 test_level2.py
```
