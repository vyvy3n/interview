"""
LLM API Rate Limiter — Token Bucket per API Key.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

The skeleton below has the loop set up for you. You fill in the branch
bodies for each level. Delete the NotImplementedError once you start.

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
        """
        # TODO (Level 3): compute elapsed seconds, add refill_rate * elapsed to
        # current_tokens, cap at max_tokens, then update last_action_ts.
        raise NotImplementedError(
            "apply_refill — implement lazy refill in Level 3 (spec/level3.md)"
        )


def solution(queries: list[list[str]]) -> list[str]:
    keys: dict[str, ApiKey] = {}  # key_id -> ApiKey
    out: list[str] = []

    for q in queries:
        op = q[0]

        # ── Level 1 ────────────────────────────────────────────────────────────

        if op == "REGISTER_KEY":
            # q = ["REGISTER_KEY", <ts>, <key_id>, <max_tokens>]
            _, ts, key_id, max_tokens = q
            # TODO: Register key with bucket = max_tokens (full).
            #       Return "true" if new, "false" if already exists.
            raise NotImplementedError(
                "REGISTER_KEY — see spec/level1.md"
            )

        elif op == "CONSUME":
            # q = ["CONSUME", <ts>, <key_id>, <tokens>]
            _, ts, key_id, tokens = q
            # TODO (L1): If key missing or bucket < tokens → return "".
            #            Otherwise deduct tokens, return remaining as string.
            # TODO (L3): Apply refill BEFORE checking/consuming.
            raise NotImplementedError(
                "CONSUME — see spec/level1.md (refill semantics added in L3)"
            )

        elif op == "GET_REMAINING":
            # q = ["GET_REMAINING", <ts>, <key_id>]
            _, ts, key_id = q
            # TODO (L1): Return current bucket level as string. "" if missing.
            # TODO (L3): Apply refill before reading.
            raise NotImplementedError(
                "GET_REMAINING — see spec/level1.md (refill semantics added in L3)"
            )

        # ── Level 2 ────────────────────────────────────────────────────────────

        elif op == "TOTAL_CONSUMED":
            # q = ["TOTAL_CONSUMED", <ts>, <key_id>]
            _, ts, key_id = q
            # TODO (L2): Return cumulative tokens successfully consumed. "" if missing.
            # TODO (L3): Apply refill before returning (keeps last_action_ts current).
            raise NotImplementedError(
                "TOTAL_CONSUMED — see spec/level2.md (refill semantics added in L3)"
            )

        elif op == "TOP_K_CONSUMERS":
            # q = ["TOP_K_CONSUMERS", <ts>, <k>]
            _, ts, k = q
            # TODO: Return top-k keys by total_consumed DESC, ties by key_id ASC.
            #       Format: "key1(total1), key2(total2), ..."
            #       If no keys: return "". If fewer than k keys, return all.
            raise NotImplementedError(
                "TOP_K_CONSUMERS — see spec/level2.md"
            )

        # ── Level 3 ────────────────────────────────────────────────────────────

        elif op == "SET_REFILL_RATE":
            # q = ["SET_REFILL_RATE", <ts>, <key_id>, <tokens_per_second>]
            _, ts, key_id, tokens_per_second = q
            # TODO: If key missing → return "false".
            #       FIRST refill bucket using the OLD rate up to ts.
            #       THEN set refill_rate = int(tokens_per_second).
            #       Update last_action_ts = int(ts). Return "true".
            raise NotImplementedError(
                "SET_REFILL_RATE — see spec/level3.md"
            )

        # ── Level 4 ────────────────────────────────────────────────────────────

        elif op == "UPGRADE_TIER":
            # q = ["UPGRADE_TIER", <ts>, <key_id>, <new_max>, <new_rate>]
            _, ts, key_id, new_max, new_rate = q
            # TODO: If key missing → return "".
            #       1. Refill bucket using OLD rate up to ts (capped at OLD max).
            #       2. Set max_tokens = int(new_max).
            #       3. If current_tokens > new_max, cap current_tokens to new_max.
            #       4. Set refill_rate = int(new_rate).
            #       5. Update last_action_ts = int(ts).
            #       Return current_tokens as string.
            raise NotImplementedError(
                "UPGRADE_TIER — see spec/level4.md"
            )

        elif op == "MERGE_KEYS":
            # q = ["MERGE_KEYS", <ts>, <surviving_key>, <absorbed_key>]
            _, ts, surviving_key, absorbed_key = q
            # TODO: Return "" if either key missing OR surviving_key == absorbed_key.
            #       1. Refill surviving_key with its own rate up to ts.
            #       2. Refill absorbed_key with its own rate up to ts.
            #       3. surviving.max_tokens += absorbed.max_tokens
            #       4. surviving.current_tokens += absorbed.current_tokens
            #          (cap at new combined max if needed)
            #       5. surviving.total_consumed += absorbed.total_consumed
            #       6. surviving.refill_rate = max(surviving.refill_rate, absorbed.refill_rate)
            #       7. surviving.last_action_ts = int(ts)
            #       8. Delete absorbed_key from keys dict.
            #       Return "true".
            raise NotImplementedError(
                "MERGE_KEYS — see spec/level4.md"
            )

        else:
            raise ValueError(f"Unknown operation: {op!r}")

    return out
