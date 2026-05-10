# Level 4 — NS fallback + error handling

## Two new things

### (a) Multiple NS records

The `authority` list can now have **multiple** NS records, and each one *may or may not* have matching glue. Try them in order and stop at the first one that lets you continue.

```
authority=[
    DNSRecord(name='deadns.com.', rdtype='NS', rdata='ns1.deadns.com.'),
    DNSRecord(name='deadns.com.', rdtype='NS', rdata='ns2.deadns.com.'),
]
additional=[
    DNSRecord(name='ns1.deadns.com.', rdtype='A', rdata='192.0.2.1'),
    DNSRecord(name='ns2.deadns.com.', rdtype='A', rdata='192.0.2.2'),
]
```

If `192.0.2.1` returns `REFUSED` (see below), fall back to `192.0.2.2`. If a NS has no glue **and** recursive resolution of its name fails, skip it and try the next NS. If **all** NS records fail to help, return `None`.

### (b) Status codes other than NOERROR

So far every response was `status='NOERROR'`. Two more statuses now appear:

| Status | Meaning | What you do |
|---|---|---|
| `NOERROR` | Server handled the query. Look at `answer` / `authority` / `additional`. | (Level 1 logic) |
| `NXDOMAIN` | This name **definitely does not exist** in this zone. | Return `None` immediately — no point trying another NS. |
| `REFUSED` | This server can't help (wrong zone). | Try the next NS in `authority`. |

## Sketch

```python
def walk(name, server):
    while True:
        resp = send_query(name, server)
        if resp.status == 'NXDOMAIN':
            return None
        if resp.status == 'REFUSED':
            return SENTINEL_TRY_NEXT_NS   # only meaningful when you're inside an NS-fallback loop
        # NOERROR
        if resp.answer is not None:
            return resp.answer
        # iterate authority NSes, following the first one that works
        for ns_record in resp.authority:
            next_ip = glue_ip_for(ns_record.rdata, resp.additional) or resolve(ns_record.rdata)
            if next_ip is None:
                continue
            ...
```

The exact control flow is up to you; the test only cares about correctness.

## Edge cases the tests check

- All NS records have glue, first works → use first.
- First NS returns `REFUSED`, second succeeds → use second.
- One NS has glue, the other needs recursive resolution → both work, prefer the one with glue.
- All NS records fail → return `None`.
- `NXDOMAIN` from any server in the chain → return `None` immediately.

## Don't worry about

- Cycles — Level 5.

## Run

```bash
python3 test_level4.py
```
