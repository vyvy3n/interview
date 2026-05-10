"""
Problem 14: LLM API Gateway
============================

Implement the LLMGateway class below. Work level by level:
  - Level 1: register_user / handle_request / get_request_count / get_total_tokens_used
  - Level 2: top_k_users_by_tokens / top_k_users_by_requests / get_users_in_tier / get_total_requests
  - Level 3: set_tier_limits / handle_request_at / get_remaining_tokens_at / update_user_tier
  - Level 4: handle_cached_request / get_cache_size / get_cache_hits / invalidate_cache / get_cache_hit_rate
  - Level 5: async versions of key methods with asyncio.Lock
  - Level 6: abatch_handle / amerge_users / acompare_and_handle (atomic compound ops)

Run tests:
  python3 test_level1.py    # ... through test_level6.py
"""

import asyncio


_DEFAULT_MAX_TOKENS = 1_000_000
_DEFAULT_REFILL_RATE = 0


class _UserRecord:
    """Internal record for a single user."""

    __slots__ = (
        "user_id",
        "tier",
        "request_count",
        "total_tokens_used",
        "cache_hits",
        # token bucket fields
        "max_tokens",
        "current_tokens",
        "refill_rate",
        "last_action_ts",
    )

    def __init__(self, user_id: str, tier: str, max_tokens: int, refill_rate: int):
        self.user_id = user_id
        self.tier = tier
        self.request_count = 0
        self.total_tokens_used = 0
        self.cache_hits = 0
        self.max_tokens = max_tokens
        self.current_tokens = max_tokens
        self.refill_rate = refill_rate
        self.last_action_ts = 0

    def refill(self, now: int) -> None:
        """Apply lazy refill up to now. Updates last_action_ts."""
        elapsed = now - self.last_action_ts
        if elapsed > 0 and self.refill_rate > 0:
            self.current_tokens = min(
                self.max_tokens,
                self.current_tokens + self.refill_rate * elapsed,
            )
        self.last_action_ts = now


class LLMGateway:
    def __init__(self):
        # user_id -> _UserRecord
        self._users: dict[str, _UserRecord] = {}

        # tier -> (max_tokens, refill_rate)
        self._tier_limits: dict[str, tuple[int, int]] = {}

        # prompt -> response (global cache, shared across all users)
        self._cache: dict[str, str] = {}

        # cache hit tracking
        self._cache_attempts: int = 0   # total calls to handle_cached_request
        self._cache_hits_global: int = 0  # total cache hits globally

        # asyncio lock (lazy init to avoid "no event loop" issues)
        self._lock: asyncio.Lock | None = None

    # ------------------------------------------------------------------
    # Internal lock helper
    # ------------------------------------------------------------------

    def _get_lock(self) -> asyncio.Lock:
        """Return the asyncio lock, creating it lazily if needed."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_tier_limits(self, tier: str) -> tuple[int, int]:
        """Return (max_tokens, refill_rate) for a tier, with defaults."""
        return self._tier_limits.get(tier, (_DEFAULT_MAX_TOKENS, _DEFAULT_REFILL_RATE))

    # ------------------------------------------------------------------
    # LEVEL 1 — Basic request lifecycle
    # ------------------------------------------------------------------

    def register_user(self, user_id: str, tier: str) -> bool:
        """
        Register a new user with the given tier.
        Returns True if newly registered, False if user_id already exists.
        """
        if user_id in self._users:
            return False
        max_tokens, refill_rate = self._get_tier_limits(tier)
        self._users[user_id] = _UserRecord(user_id, tier, max_tokens, refill_rate)
        return True

    def handle_request(self, user_id: str, prompt: str, tokens_used: int) -> str:
        """
        Process a request WITHOUT rate limiting.
        Returns "ok" if accepted, "" if user missing.
        Tracks total tokens consumed and request count.
        """
        if user_id not in self._users:
            return ""
        user = self._users[user_id]
        user.request_count += 1
        user.total_tokens_used += tokens_used
        return "ok"

    def get_request_count(self, user_id: str) -> int:
        """Total successful requests by user. Returns -1 if missing."""
        if user_id not in self._users:
            return -1
        return self._users[user_id].request_count

    def get_total_tokens_used(self, user_id: str) -> int:
        """Cumulative tokens consumed. Returns -1 if missing."""
        if user_id not in self._users:
            return -1
        return self._users[user_id].total_tokens_used

    # ------------------------------------------------------------------
    # LEVEL 2 — Usage tracking + reports
    # ------------------------------------------------------------------

    def top_k_users_by_tokens(self, k: int) -> list[tuple[str, int]]:
        """
        Top k users by total tokens used, DESC.
        Ties broken by user_id alphabetical ASC.
        Returns list of (user_id, total_tokens).
        """
        users = sorted(
            self._users.values(),
            key=lambda u: (-u.total_tokens_used, u.user_id),
        )
        return [(u.user_id, u.total_tokens_used) for u in users[:k]]

    def top_k_users_by_requests(self, k: int) -> list[tuple[str, int]]:
        """
        Top k users by request count, DESC.
        Ties broken by user_id alphabetical ASC.
        Returns list of (user_id, request_count).
        """
        users = sorted(
            self._users.values(),
            key=lambda u: (-u.request_count, u.user_id),
        )
        return [(u.user_id, u.request_count) for u in users[:k]]

    def get_users_in_tier(self, tier: str) -> list[str]:
        """Users in given tier, sorted alphabetically."""
        return sorted(u.user_id for u in self._users.values() if u.tier == tier)

    def get_total_requests(self) -> int:
        """Global total request count across all users."""
        return sum(u.request_count for u in self._users.values())

    # ------------------------------------------------------------------
    # LEVEL 3 — Token-bucket rate limiting (lazy refill)
    # ------------------------------------------------------------------

    def set_tier_limits(self, tier: str, max_tokens: int, refill_per_sec: int) -> bool:
        """
        Set a tier's bucket capacity and refill rate.
        Returns True always (even if no users in this tier yet).
        Applied retroactively to existing users in this tier too.
        """
        self._tier_limits[tier] = (max_tokens, refill_per_sec)
        # Apply to all existing users in this tier
        for user in self._users.values():
            if user.tier == tier:
                user.max_tokens = max_tokens
                user.refill_rate = refill_per_sec
                # Cap current tokens at new max
                user.current_tokens = min(user.current_tokens, max_tokens)
        return True

    def handle_request_at(
        self, user_id: str, prompt: str, tokens_used: int, now: int
    ) -> str:
        """
        Like handle_request but WITH rate limiting and explicit timestamp.
        First refills bucket, then checks if enough tokens available.
        Returns "ok" if accepted, "rate_limited" if not, "" if user missing.
        """
        return self._do_handle_request_at(user_id, prompt, tokens_used, now)

    def _do_handle_request_at(
        self, user_id: str, prompt: str, tokens_used: int, now: int
    ) -> str:
        if user_id not in self._users:
            return ""
        user = self._users[user_id]
        user.refill(now)
        if user.current_tokens < tokens_used:
            return "rate_limited"
        user.current_tokens -= tokens_used
        user.request_count += 1
        user.total_tokens_used += tokens_used
        return "ok"

    def get_remaining_tokens_at(self, user_id: str, now: int) -> int:
        """
        Triggers refill, returns current bucket level.
        Returns -1 if user missing.
        """
        return self._do_get_remaining_tokens_at(user_id, now)

    def _do_get_remaining_tokens_at(self, user_id: str, now: int) -> int:
        if user_id not in self._users:
            return -1
        user = self._users[user_id]
        user.refill(now)
        return user.current_tokens

    def update_user_tier(self, user_id: str, new_tier: str, now: int) -> bool:
        """
        Refill first using current rate, then switch to new_tier's limits.
        Caps current_tokens at new max.
        Returns True if updated, False if user missing.
        """
        return self._do_update_user_tier(user_id, new_tier, now)

    def _do_update_user_tier(self, user_id: str, new_tier: str, now: int) -> bool:
        if user_id not in self._users:
            return False
        user = self._users[user_id]
        user.refill(now)
        new_max, new_rate = self._get_tier_limits(new_tier)
        user.tier = new_tier
        user.max_tokens = new_max
        user.refill_rate = new_rate
        user.current_tokens = min(user.current_tokens, new_max)
        return True

    # ------------------------------------------------------------------
    # LEVEL 4 — Per-prompt response caching
    # ------------------------------------------------------------------

    def handle_cached_request(
        self,
        user_id: str,
        prompt: str,
        response: str,
        tokens_used: int,
        now: int,
    ) -> str:
        """
        Like handle_request_at but with caching.
        - Cache hit: no token deduction, increment cache_hits, return cached response.
        - Cache miss + accepted: store response, return "ok".
        - Cache miss + rate_limited: return "rate_limited".
        - User missing: return "".
        """
        return self._do_handle_cached_request(user_id, prompt, response, tokens_used, now)

    def _do_handle_cached_request(
        self,
        user_id: str,
        prompt: str,
        response: str,
        tokens_used: int,
        now: int,
    ) -> str:
        self._cache_attempts += 1
        if user_id not in self._users:
            return ""
        # Cache hit — serve from cache, no token deduction
        if prompt in self._cache:
            user = self._users[user_id]
            user.cache_hits += 1
            self._cache_hits_global += 1
            return self._cache[prompt]
        # Cache miss — run rate-limit check
        result = self._do_handle_request_at(user_id, prompt, tokens_used, now)
        if result == "ok":
            self._cache[prompt] = response
        return result

    def get_cache_size(self) -> int:
        """Total number of cached prompts."""
        return len(self._cache)

    def get_cache_hits(self, user_id: str) -> int:
        """Cache hits attributed to user. Returns -1 if missing."""
        if user_id not in self._users:
            return -1
        return self._users[user_id].cache_hits

    def invalidate_cache(self, prefix: str) -> int:
        """
        Delete all cached entries whose prompt starts with prefix.
        Returns count deleted.
        """
        return self._do_invalidate_cache(prefix)

    def _do_invalidate_cache(self, prefix: str) -> int:
        to_delete = [p for p in self._cache if p.startswith(prefix)]
        for p in to_delete:
            del self._cache[p]
        return len(to_delete)

    def get_cache_hit_rate(self) -> str:
        """
        Global hit rate as "X/Y" (hits/total_attempts).
        Returns "0/0" if no attempts.
        """
        return f"{self._cache_hits_global}/{self._cache_attempts}"

    # ------------------------------------------------------------------
    # LEVEL 5 — Async concurrent request handling (asyncio)
    # ------------------------------------------------------------------

    async def aregister_user(self, user_id: str, tier: str) -> bool:
        """Async register_user. Acquires lock."""
        async with self._get_lock():
            return self.register_user(user_id, tier)

    async def ahandle_request_at(
        self, user_id: str, prompt: str, tokens_used: int, now: int
    ) -> str:
        """Async handle_request_at. Acquires lock."""
        async with self._get_lock():
            return self._do_handle_request_at(user_id, prompt, tokens_used, now)

    async def ahandle_cached_request(
        self,
        user_id: str,
        prompt: str,
        response: str,
        tokens_used: int,
        now: int,
    ) -> str:
        """Async handle_cached_request. Acquires lock."""
        async with self._get_lock():
            return self._do_handle_cached_request(user_id, prompt, response, tokens_used, now)

    async def aget_remaining_tokens_at(self, user_id: str, now: int) -> int:
        """Async get_remaining_tokens_at. Acquires lock."""
        async with self._get_lock():
            return self._do_get_remaining_tokens_at(user_id, now)

    # ------------------------------------------------------------------
    # LEVEL 6 — Atomic compound operations
    # ------------------------------------------------------------------

    async def abatch_handle(
        self,
        user_id: str,
        requests: list[tuple[str, int]],
        now: int,
    ) -> int:
        """
        Atomically process a list of (prompt, tokens) requests.
        ALL must fit in the user's current bucket (after lazy refill).
        If yes: deduct ALL tokens, count ALL as accepted, return count.
        If any one would exceed bucket: reject ALL, return -1.
        Returns -1 if user missing.
        """
        async with self._get_lock():
            if user_id not in self._users:
                return -1
            user = self._users[user_id]
            user.refill(now)
            total_needed = sum(tokens for _, tokens in requests)
            if user.current_tokens < total_needed:
                return -1
            # All fit — commit
            user.current_tokens -= total_needed
            count = len(requests)
            user.request_count += count
            user.total_tokens_used += total_needed
            return count

    async def amerge_users(self, survivor: str, absorbed: str) -> bool:
        """
        Atomically merge absorbed into survivor.
        - max_tokens: sum
        - current_tokens: sum (capped at new max)
        - refill_rate: max of the two
        - request_count, total_tokens_used, cache_hits: sum
        - tier: keep survivor's
        - Absorbed is deleted.
        Returns False if either is missing or they are the same user.
        """
        async with self._get_lock():
            if survivor == absorbed:
                return False
            if survivor not in self._users or absorbed not in self._users:
                return False
            s = self._users[survivor]
            a = self._users[absorbed]
            new_max = s.max_tokens + a.max_tokens
            new_current = min(s.current_tokens + a.current_tokens, new_max)
            new_rate = max(s.refill_rate, a.refill_rate)
            s.max_tokens = new_max
            s.current_tokens = new_current
            s.refill_rate = new_rate
            s.request_count += a.request_count
            s.total_tokens_used += a.total_tokens_used
            s.cache_hits += a.cache_hits
            del self._users[absorbed]
            return True

    async def acompare_and_handle(
        self,
        user_id: str,
        prompt: str,
        expected_remaining: int,
        tokens_used: int,
        now: int,
    ) -> str:
        """
        Atomically: refill, then if current_tokens == expected_remaining,
        handle (deduct + count, return "ok"). Else return "stale".
        Returns "" if user missing.
        """
        async with self._get_lock():
            if user_id not in self._users:
                return ""
            user = self._users[user_id]
            user.refill(now)
            if user.current_tokens != expected_remaining:
                return "stale"
            if user.current_tokens < tokens_used:
                return "rate_limited"
            user.current_tokens -= tokens_used
            user.request_count += 1
            user.total_tokens_used += tokens_used
            return "ok"
