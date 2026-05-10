# Level 7 — Step 7: Parallel resolution

> Verbatim from the assessment.

Make `resolve_all()` resolve domains concurrently to complete faster in wall-clock time.

- At most `max_workers` (default 5) calls to `send_query` may be in-flight at any time.
- If a query is already in-flight from another domain's resolution, wait for it rather than sending a duplicate.

```
./test.sh 7
```

`[execution time limit] 30 seconds`
`[memory limit] 4g`
