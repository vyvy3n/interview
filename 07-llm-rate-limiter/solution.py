"""
LLM API Rate Limiter — Token Bucket per API Key.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

Level 1: REGISTER_KEY, CONSUME, GET_REMAINING         — see spec/level1.md
Level 2: TOTAL_CONSUMED, TOP_K_CONSUMERS              — see spec/level2.md
Level 3: SET_REFILL_RATE (+ lazy refill on all ops)   — see spec/level3.md
Level 4: UPGRADE_TIER, MERGE_KEYS                     — see spec/level4.md
"""


class ApiKey:
    """Represents one API key and its token bucket."""

    def __init__(self, key_id: str, max_tokens: int, registered_ts: int):
        self.key_id = key_id
        self.max_tokens = max_tokens
        self.current_tokens = max_tokens   # bucket starts full
        self.total_consumed = 0            # cumulative successful consume total
        self.refill_rate = 0               # tokens per second; 0 = no refill (L3)
        self.last_action_ts = registered_ts  # for lazy refill computation (L3)

    def apply_refill(self, current_ts: int) -> None:
        """Lazily refill the bucket up to current_ts using the current refill_rate.

        Call this at the START of every operation that touches the bucket.
        Updates last_action_ts to current_ts after refilling.
        All arithmetic is integer — no floats.
        """
        elapsed = current_ts - self.last_action_ts
        self.current_tokens = min(
            self.max_tokens,
            self.current_tokens + self.refill_rate * elapsed,
        )
        self.last_action_ts = current_ts


def solution(queries: list[list[str]]) -> list[str]:
    keys: dict[str, ApiKey] = {}  # key_id -> ApiKey
    out: list[str] = []

    for q in queries:
        op = q[0]

        # ── Level 1 ────────────────────────────────────────────────────────────

        if op == "REGISTER_KEY":
            # q = ["REGISTER_KEY", <ts>, <key_id>, <max_tokens>]
            _, ts, key_id, max_tokens = q
            if key_id in keys:
                out.append("false")
            else:
                keys[key_id] = ApiKey(key_id, int(max_tokens), int(ts))
                out.append("true")

        elif op == "CONSUME":
            # q = ["CONSUME", <ts>, <key_id>, <tokens>]
            _, ts, key_id, tokens = q
            if key_id not in keys:
                out.append("")
            else:
                key = keys[key_id]
                key.apply_refill(int(ts))
                cost = int(tokens)
                if key.current_tokens >= cost:
                    key.current_tokens -= cost
                    key.total_consumed += cost
                    out.append(str(key.current_tokens))
                else:
                    out.append("")

        elif op == "GET_REMAINING":
            # q = ["GET_REMAINING", <ts>, <key_id>]
            _, ts, key_id = q
            if key_id not in keys:
                out.append("")
            else:
                key = keys[key_id]
                key.apply_refill(int(ts))
                out.append(str(key.current_tokens))

        # ── Level 2 ────────────────────────────────────────────────────────────

        elif op == "TOTAL_CONSUMED":
            # q = ["TOTAL_CONSUMED", <ts>, <key_id>]
            _, ts, key_id = q
            if key_id not in keys:
                out.append("")
            else:
                key = keys[key_id]
                # Refill to advance last_action_ts even though we only read total
                key.apply_refill(int(ts))
                out.append(str(key.total_consumed))

        elif op == "TOP_K_CONSUMERS":
            # q = ["TOP_K_CONSUMERS", <ts>, <k>]
            _, ts, k = q
            if not keys:
                out.append("")
            else:
                # Sort by total_consumed DESC, then key_id ASC for ties
                ranked = sorted(
                    keys.values(),
                    key=lambda x: (-x.total_consumed, x.key_id),
                )
                top = ranked[: int(k)]
                out.append(", ".join(f"{x.key_id}({x.total_consumed})" for x in top))

        # ── Level 3 ────────────────────────────────────────────────────────────

        elif op == "SET_REFILL_RATE":
            # q = ["SET_REFILL_RATE", <ts>, <key_id>, <tokens_per_second>]
            _, ts, key_id, tokens_per_second = q
            if key_id not in keys:
                out.append("false")
            else:
                key = keys[key_id]
                # Refill using OLD rate first, then set new rate
                key.apply_refill(int(ts))
                key.refill_rate = int(tokens_per_second)
                out.append("true")

        # ── Level 4 ────────────────────────────────────────────────────────────

        elif op == "UPGRADE_TIER":
            # q = ["UPGRADE_TIER", <ts>, <key_id>, <new_max>, <new_rate>]
            _, ts, key_id, new_max, new_rate = q
            if key_id not in keys:
                out.append("")
            else:
                key = keys[key_id]
                ts_int = int(ts)
                # 1. Refill using OLD rate (capped at OLD max inside apply_refill)
                key.apply_refill(ts_int)
                # 2. Update max_tokens
                key.max_tokens = int(new_max)
                # 3. Cap current_tokens to new max if needed
                if key.current_tokens > key.max_tokens:
                    key.current_tokens = key.max_tokens
                # 4. Set new refill rate
                key.refill_rate = int(new_rate)
                # last_action_ts was already set by apply_refill
                out.append(str(key.current_tokens))

        elif op == "MERGE_KEYS":
            # q = ["MERGE_KEYS", <ts>, <surviving_key>, <absorbed_key>]
            _, ts, surviving_key, absorbed_key = q
            # Reject self-merge or either key missing
            if (surviving_key == absorbed_key
                    or surviving_key not in keys
                    or absorbed_key not in keys):
                out.append("")
            else:
                ts_int = int(ts)
                s = keys[surviving_key]
                a = keys[absorbed_key]
                # 1 & 2. Refill both keys independently
                s.apply_refill(ts_int)
                a.apply_refill(ts_int)
                # 3. Combine max
                s.max_tokens += a.max_tokens
                # 4. Combine tokens, cap at new combined max
                s.current_tokens = min(s.max_tokens, s.current_tokens + a.current_tokens)
                # 5. Combine total consumed
                s.total_consumed += a.total_consumed
                # 6. Take the higher refill rate
                s.refill_rate = max(s.refill_rate, a.refill_rate)
                # 7. last_action_ts already set by apply_refill on surviving key
                # 8. Delete absorbed key
                del keys[absorbed_key]
                out.append("true")

        else:
            raise ValueError(f"Unknown operation: {op!r}")

    return out
