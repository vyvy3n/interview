# Level 2 — Step 2: CNAME records

> Verbatim from the assessment.

Sometimes, instead of containing an `A` record, the `answer` section will contain a `CNAME` record.

For example, when resolving `www.example.com`, the authoritative server returns:

```
DNSResponse(
    status="NOERROR",
    answer=DNSRecord(name="www.example.com.", rdtype="CNAME",
                     rdata="example.com."),
    authority=[],
    additional=[]
)
```

This means we have to start the process over from the root server, but instead of looking for `www.example.com`, we're now looking for a different name stored in this `rdata` field: `example.com.`.

`CNAME` chains can be longer than one hop. For example, `store.example.com` aliases to `shop.fastcdn.net`, which itself aliases to `cdn.fastcdn.net`, which finally has an `A` record.

Add handling for this case to `resolve()` and test your code with:

```
./test.sh 2
```
