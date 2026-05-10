# Level 5 — Step 5: Cycle Handling

> Verbatim from the assessment.

Properly configured DNS should not contain cycles, but in practice these can happen by accident in two ways:

- `CNAME` chains (`A` aliases to `B` which aliases back to `A`).
- Glue lookups (zone A's `NS` is in zone B, and zone B's `NS` is in zone A).

Implement a basic form of cycle detection: if we haven't succeeded after `max_queries` calls to `send_query`, assume we're caught in a cycle and return `None`.

```
./test.sh 5
```
