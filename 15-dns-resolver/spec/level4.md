# Level 4 — Step 4: Error handling and NS fallback

> Verbatim from the assessment.

Now, in the `authority` section: there can be multiple `NS` records, and each `NS` record may or may not have a matching glue record. We will try each nameserver in order until one succeeds.

So far every query has returned `status="NOERROR"`, but there are two other statuses we'll handle.

- `NXDOMAIN` means you're asking the right server, but the name definitely doesn't exist in this zone. In this case, there's no point trying another NS — we can just return `None`.
- `REFUSED` means for whatever reason, the server can't help you and does not know about this name. In this case we need to try the next nameserver if available.

For example, resolving `deadns.com`, the `.com` TLD returns two NS records with glue:

```
DNSResponse(
    status="NOERROR",
    answer=None,
    authority=[DNSRecord(name="deadns.com.", rdtype="NS",
                         rdata="ns1.deadns.com."),
                DNSRecord(name="deadns.com.", rdtype="NS",
                          rdata="ns2.deadns.com.")],
    additional=[DNSRecord(name="ns1.deadns.com.", rdtype="AAAA",
                          rdata="2001:db8::1"),
                DNSRecord(name="ns1.deadns.com.", rdtype="A",
                          rdata="192.0.2.1"),
                DNSRecord(name="ns2.deadns.com.", rdtype="AAAA",
                          rdata="2001:db8::2"),
                DNSRecord(name="ns2.deadns.com.", rdtype="A",
                          rdata="192.0.2.2")]
)
```

Querying the first nameserver at `192.0.2.1` returns `status="REFUSED"` — so we fall back to the second NS at `192.0.2.2`, which succeeds.

Edge case: if a nameserver has no glue and we fail to resolve its IP, skip it and try the next NS. If all the nameservers fail to help us, we return `None`.

```
./test.sh 4
```
