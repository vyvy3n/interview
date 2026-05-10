# Level 1 — Step 0 (Normalize) + Step 1 (Annotated Example)

> Verbatim from the assessment. Combined here because passing Step 1 tests requires `normalize()` from Step 0.

## Step 0 - Normalize

In DNS, names are case insensitive, and by convention always end in a trailing dot. For example, `"Anthropic.COM"` normalizes to `"anthropic.com."`.

```
>>> normalize("Anthropic.COM")
'anthropic.com.'
>>> normalize("Docs.Anthropic.Com")
'docs.anthropic.com.'
>>> normalize("ANTHROPIC.COM")
'anthropic.com.'
```

Implement `normalize()` in `dns_exercise.py`. You can run all Step 0 tests with:

```
./test.sh 0
```

You can read the tests in `tests/test_dns.py` and you can run an individual test with `pytest -k test_function_name`. For example:

```
pytest -k test_normalize_trailing_dot
```

## Step 1 - Annotated Example

For concreteness, we'll start with an annotated example and show the actual responses to help you get a feel for how DNS works.

Suppose you type `"Anthropic.COM"` into your web browser. With your `normalize()` function, the normalized name is `anthropic.com.`.

We've provided a function `send_query(normalized_name, server_ip)` that simulates the network call to `server_ip` and the IP address of a "root server" which is the starting point of any DNS query.

`send_query("anthropic.com.", ROOT_SERVER)` returns:

```
DNSResponse(
    status="NOERROR",
    answer=None,
    authority=[DNSRecord(name="com.", rdtype="NS",
                         rdata="a.gtld-servers.net.")],
    additional=[DNSRecord(name="a.gtld-servers.net.", rdtype="AAAA",
                          rdata="2001:db8::1"),
                DNSRecord(name="a.gtld-servers.net.", rdtype="A",
                          rdata="192.5.6.30")]
)
```

The root server query succeeded with `NOERROR`, but `answer` is `None` — it doesn't know the IP address. But it does know another server who can help us! The `NS` type record says that the server named `a.gtld-servers.net.` knows more about `com.` names.

But `send_query` needs an IP address — what is the IP for `a.gtld-servers.net.`? Helpfully, this response contains "glue records" in the `additional` field. We need the one with `rdtype="A"` — that's the IPv4 address. (The `AAAA` record is IPv6, which we'll ignore.)

For now we'll assume there is only one `NS` record in `authority`, and that the name in `rdata` has exactly one matching glue record. So the next step on our journey is to ask `192.5.6.30`:

`send_query("anthropic.com.", "192.5.6.30")` returns:

```
DNSResponse(
    status="NOERROR",
    answer=None,
    authority=[DNSRecord(name="anthropic.com.", rdtype="NS",
                         rdata="isla.ns.cloudflare.com.")],
    additional=[DNSRecord(name="isla.ns.cloudflare.com.", rdtype="AAAA",
                          rdata="2001:db8::1"),
                DNSRecord(name="isla.ns.cloudflare.com.", rdtype="A",
                          rdata="108.162.192.119")]
)
```

Exactly as before, this server doesn't know the IP address we're looking for, but again it can point us in the right direction.

`send_query("anthropic.com.", "108.162.192.119")` returns:

```
DNSResponse(
    status="NOERROR",
    answer=DNSRecord(name="anthropic.com.", rdtype="A",
                     rdata="160.79.104.10"),
    authority=[],
    additional=[]
)
```

Finally, our long journey is over. The `answer` field holds a type `A` record (remember, `A` means "my rdata field holds the IP for this name"), and we return its `rdata`.

Now implement `resolve()` in `dns_exercise.py` so that the provided unit tests pass for Step 1. Test Step 1 from Terminal with:

```
./test.sh 1
```

Don't worry about handling any cases not covered by the tests; we'll get to those in future steps. For now, assume every query returns `status="NOERROR"`. Feel free to define additional helper functions.

If you get a status of `NXDOMAIN`, this means "the name you asked for definitely doesn't exist". Check your normalization.
