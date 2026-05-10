# Level 3 — Step 3: Missing glue records

> Verbatim from the assessment.

Sometimes we are directed to a nameserver whose IP isn't in the `additional` section. When there is no matching glue record, you must **resolve the nameserver's IP address** before continuing.

For example, when we try to resolve `api.anthropic.com`:

```
DNSResponse(
    status="NOERROR",
    answer=None,
    authority=[DNSRecord(name="api.anthropic.com.", rdtype="NS",
                         rdata="gemma.ns.cloudflare.com.")],
    additional=[]
)
```

The `authority` says to ask `gemma.ns.cloudflare.com.`, but `additional` is empty — this server doesn't know the IP for `gemma.ns.cloudflare.com.`. So we need to resolve `gemma.ns.cloudflare.com.` first (starting from the root server, just like any other resolution) to get its IP, then continue resolving `api.anthropic.com`.

For this step, still assume there is exactly one `NS` record in `authority`.

```
./test.sh 3
```
