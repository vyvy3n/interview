"""
LLM Conversation Service
========================
Implement the ConversationService class across 6 levels.

Level guide:
  L1: create_conversation, add_message, get_messages,
      get_message_count, delete_conversation          -> spec/level1.md
  L2: list_user_conversations, top_k_active,
      get_user_total_tokens                           -> spec/level2.md
  L3: set_context_limit, add_message_with_budget,
      summarize_to_budget                             -> spec/level3.md
  L4: fork_conversation, branch_at_message,
      merge_conversations                             -> spec/level4.md
  L5: thread-safe + start_session_workers,
      stop_session_workers, queue_message,
      wait_for_processed                              -> spec/level5.md
  L6: compare_and_swap_message, batch_add_messages,
      wait_for_message_count                          -> spec/level6.md
"""

import threading
import queue
import time


class ConversationService:
    def __init__(self):
        # conversations: conv_id -> {
        #   "user_id": str,
        #   "messages": list of {"role": str, "content": str, "tokens": int, "ts": int},
        #   "total_tokens": int,
        #   "max_tokens": int | None,
        # }
        self._conversations = {}

        # global monotonic message timestamp counter
        self._msg_counter = 0

        # threading (L5+)
        self._lock = threading.RLock()

        # L6: condition variable for wait_for_message_count
        self._msg_condition = threading.Condition(self._lock)

        # L5: worker thread pool
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._workers = []

        # L5: queue item tracking
        self._queue_items = {}   # queue_id -> {"event": threading.Event, "done": bool}
        self._queue_counter = 0  # global counter for q_1, q_2, ...

    # ------------------------------------------------------------------ #
    # Internal helpers                                                      #
    # ------------------------------------------------------------------ #

    def _next_ts(self) -> int:
        """Return a monotonically increasing timestamp for message ordering."""
        self._msg_counter += 1
        return self._msg_counter

    # ------------------------------------------------------------------ #
    # Level 1 — Basic Conversation Lifecycle                                #
    # ------------------------------------------------------------------ #

    def create_conversation(self, conv_id: str, user_id: str) -> bool:
        """Create a new conversation. Returns True if created, False if conv_id exists."""
        with self._lock:
            if conv_id in self._conversations:
                return False
            self._conversations[conv_id] = {
                "user_id": user_id,
                "messages": [],
                "total_tokens": 0,
                "max_tokens": None,
            }
            return True

    def add_message(self, conv_id: str, role: str, content: str, tokens: int) -> int:
        """Append a message to the conversation. Returns cumulative token total, or -1 if missing."""
        with self._lock:
            if conv_id not in self._conversations:
                return -1
            conv = self._conversations[conv_id]
            ts = self._next_ts()
            conv["messages"].append({"role": role, "content": content, "tokens": tokens, "ts": ts})
            conv["total_tokens"] += tokens
            # Notify waiters (L6)
            self._msg_condition.notify_all()
            return conv["total_tokens"]

    def get_messages(self, conv_id: str) -> list:
        """Return list of 'role:content' strings in chronological order. [] if missing."""
        with self._lock:
            if conv_id not in self._conversations:
                return []
            return [f"{m['role']}:{m['content']}" for m in self._conversations[conv_id]["messages"]]

    def get_message_count(self, conv_id: str) -> int:
        """Return message count, or -1 if missing."""
        with self._lock:
            if conv_id not in self._conversations:
                return -1
            return len(self._conversations[conv_id]["messages"])

    def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation. Returns True if deleted, False if missing."""
        with self._lock:
            if conv_id not in self._conversations:
                return False
            del self._conversations[conv_id]
            return True

    # ------------------------------------------------------------------ #
    # Level 2 — User-level Activity Reports                                 #
    # ------------------------------------------------------------------ #

    def list_user_conversations(self, user_id: str) -> list:
        """Return conv_ids owned by user_id, sorted alphabetically."""
        with self._lock:
            return sorted(
                cid for cid, conv in self._conversations.items()
                if conv["user_id"] == user_id
            )

    def top_k_active(self, k: int) -> list:
        """Return top-k conversations by message count (desc), ties broken by conv_id (asc).
        Returns list of (conv_id, message_count) tuples."""
        with self._lock:
            items = [(cid, len(conv["messages"])) for cid, conv in self._conversations.items()]
            # Sort: primary = -message_count (desc), secondary = conv_id (asc)
            items.sort(key=lambda x: (-x[1], x[0]))
            return items[:k]

    def get_user_total_tokens(self, user_id: str) -> int:
        """Return sum of total_tokens for all user's conversations. -1 if user has no convs."""
        with self._lock:
            user_convs = [conv for conv in self._conversations.values() if conv["user_id"] == user_id]
            if not user_convs:
                return -1
            return sum(conv["total_tokens"] for conv in user_convs)

    # ------------------------------------------------------------------ #
    # Level 3 — Context Window + Truncation                                 #
    # ------------------------------------------------------------------ #

    def set_context_limit(self, conv_id: str, max_tokens: int) -> int:
        """Set the conversation's token budget. If current total > max, drop oldest messages.
        Returns count of messages dropped, or -1 if conv missing."""
        with self._lock:
            if conv_id not in self._conversations:
                return -1
            conv = self._conversations[conv_id]
            conv["max_tokens"] = max_tokens
            dropped = 0
            while conv["total_tokens"] > max_tokens and conv["messages"]:
                oldest = conv["messages"].pop(0)
                conv["total_tokens"] -= oldest["tokens"]
                dropped += 1
            return dropped

    def add_message_with_budget(self, conv_id: str, role: str, content: str, tokens: int) -> int:
        """Add message, enforcing context limit if set.
        - If no limit: behaves like add_message but returns 0 (no drops).
        - If limit set: drop oldest until (total + new_tokens) <= max_tokens, then append.
        - If new message alone exceeds max_tokens: REJECT (no state change), return -1.
        - Returns count of messages dropped, or -1 on missing conv or rejection.
        """
        with self._lock:
            if conv_id not in self._conversations:
                return -1
            conv = self._conversations[conv_id]
            max_tokens = conv["max_tokens"]

            if max_tokens is None:
                # No limit — behave like add_message, return 0
                ts = self._next_ts()
                conv["messages"].append({"role": role, "content": content, "tokens": tokens, "ts": ts})
                conv["total_tokens"] += tokens
                self._msg_condition.notify_all()
                return 0

            # Reject if single message exceeds budget
            if tokens > max_tokens:
                return -1

            # Drop oldest until there's room
            dropped = 0
            while conv["total_tokens"] + tokens > max_tokens and conv["messages"]:
                oldest = conv["messages"].pop(0)
                conv["total_tokens"] -= oldest["tokens"]
                dropped += 1

            # Append
            ts = self._next_ts()
            conv["messages"].append({"role": role, "content": content, "tokens": tokens, "ts": ts})
            conv["total_tokens"] += tokens
            self._msg_condition.notify_all()
            return dropped

    def summarize_to_budget(self, conv_id: str, max_tokens: int) -> int:
        """Drop oldest messages until total <= max_tokens.
        Returns count of messages kept, or -1 if conv missing."""
        with self._lock:
            if conv_id not in self._conversations:
                return -1
            conv = self._conversations[conv_id]
            while conv["total_tokens"] > max_tokens and conv["messages"]:
                oldest = conv["messages"].pop(0)
                conv["total_tokens"] -= oldest["tokens"]
            return len(conv["messages"])

    # ------------------------------------------------------------------ #
    # Level 4 — Fork + Branch + Merge                                       #
    # ------------------------------------------------------------------ #

    def fork_conversation(self, source_id: str, new_id: str) -> bool:
        """Deep copy source into new_id. Returns False if source missing or new_id exists."""
        with self._lock:
            if source_id not in self._conversations:
                return False
            if new_id in self._conversations:
                return False
            source = self._conversations[source_id]
            self._conversations[new_id] = {
                "user_id": source["user_id"],
                "messages": [dict(m) for m in source["messages"]],
                "total_tokens": source["total_tokens"],
                "max_tokens": source["max_tokens"],
            }
            return True

    def branch_at_message(self, conv_id: str, msg_index: int, new_id: str) -> bool:
        """Fork conv_id keeping messages[0..msg_index] inclusive.
        Returns False if conv missing, invalid index, or new_id exists."""
        with self._lock:
            if conv_id not in self._conversations:
                return False
            if new_id in self._conversations:
                return False
            conv = self._conversations[conv_id]
            messages = conv["messages"]
            if msg_index < 0 or msg_index >= len(messages):
                return False
            kept = messages[:msg_index + 1]
            self._conversations[new_id] = {
                "user_id": conv["user_id"],
                "messages": [dict(m) for m in kept],
                "total_tokens": sum(m["tokens"] for m in kept),
                "max_tokens": conv["max_tokens"],
            }
            return True

    def merge_conversations(self, survivor: str, absorbed: str) -> bool:
        """Append absorbed's messages to survivor's, sorted by ts (ties: survivor first).
        Survivor keeps its owner and context limit. Absorbed is deleted.
        If survivor has context limit and merged total exceeds it, drop oldest.
        Returns False if either missing or same id."""
        with self._lock:
            if survivor not in self._conversations:
                return False
            if absorbed not in self._conversations:
                return False
            if survivor == absorbed:
                return False

            s_conv = self._conversations[survivor]
            a_conv = self._conversations[absorbed]

            # Merge and sort messages by ts; ties: survivor messages come first.
            # We can achieve this by tagging survivor messages with a secondary sort key of 0
            # and absorbed messages with 1.
            tagged_s = [(m["ts"], 0, m) for m in s_conv["messages"]]
            tagged_a = [(m["ts"], 1, m) for m in a_conv["messages"]]
            merged = sorted(tagged_s + tagged_a, key=lambda x: (x[0], x[1]))
            merged_messages = [m for _, _, m in merged]

            s_conv["messages"] = [dict(m) for m in merged_messages]
            s_conv["total_tokens"] = sum(m["tokens"] for m in s_conv["messages"])

            # Enforce context limit if set
            max_tokens = s_conv["max_tokens"]
            if max_tokens is not None:
                while s_conv["total_tokens"] > max_tokens and s_conv["messages"]:
                    oldest = s_conv["messages"].pop(0)
                    s_conv["total_tokens"] -= oldest["tokens"]

            del self._conversations[absorbed]
            return True

    # ------------------------------------------------------------------ #
    # Level 5 — Concurrent Sessions (Threading)                             #
    # ------------------------------------------------------------------ #

    def start_session_workers(self, count: int) -> None:
        """Spawn `count` worker threads that process queued message additions."""
        with self._lock:
            if self._workers:
                return  # already running
        self._stop_event.clear()

        def _worker():
            while True:
                try:
                    item = self._queue.get(timeout=0.05)
                except queue.Empty:
                    if self._stop_event.is_set():
                        break
                    continue

                if item is None:
                    # Sentinel value to stop the worker
                    break

                conv_id = item["conv_id"]
                role = item["role"]
                content = item["content"]
                tokens = item["tokens"]

                with self._lock:
                    if conv_id in self._conversations and self._conversations[conv_id]["max_tokens"] is not None:
                        self.add_message_with_budget(conv_id, role, content, tokens)
                    else:
                        self.add_message(conv_id, role, content, tokens)
                    # mark the queue item done
                    item["event"].set()

        for _ in range(count):
            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            self._workers.append(t)

    def stop_session_workers(self) -> None:
        """Signal workers to stop and join all threads."""
        self._stop_event.set()
        # Send sentinels to unblock blocked workers
        for _ in self._workers:
            self._queue.put(None)
        for t in self._workers:
            t.join()
        self._workers.clear()

    def queue_message(self, conv_id: str, role: str, content: str, tokens: int) -> str:
        """Enqueue an async message addition. Returns queue_id or '' if conv missing."""
        with self._lock:
            if conv_id not in self._conversations:
                return ""
            self._queue_counter += 1
            queue_id = f"q_{self._queue_counter}"
            event = threading.Event()
            item = {
                "queue_id": queue_id,
                "conv_id": conv_id,
                "role": role,
                "content": content,
                "tokens": tokens,
                "event": event,
            }
            self._queue_items[queue_id] = item
            self._queue.put(item)
            return queue_id

    def wait_for_processed(self, queue_id: str, timeout: float = None) -> bool:
        """Block until the queued item is processed or timeout.
        Returns True if processed, False on timeout or unknown id."""
        with self._lock:
            item = self._queue_items.get(queue_id)
        if item is None:
            return False
        event = item["event"]
        return event.wait(timeout=timeout)

    # ------------------------------------------------------------------ #
    # Level 6 — Atomic Compound Operations                                  #
    # ------------------------------------------------------------------ #

    def compare_and_swap_message(self, conv_id: str, msg_index: int,
                                  expected_content: str, new_content: str,
                                  new_tokens: int) -> bool:
        """Atomically: if messages[msg_index].content == expected_content, update it.
        Adjusts cumulative token total accordingly.
        Returns False if conv missing, invalid index, or content mismatch."""
        with self._lock:
            if conv_id not in self._conversations:
                return False
            conv = self._conversations[conv_id]
            messages = conv["messages"]
            if msg_index < 0 or msg_index >= len(messages):
                return False
            msg = messages[msg_index]
            if msg["content"] != expected_content:
                return False
            # Swap
            old_tokens = msg["tokens"]
            msg["content"] = new_content
            msg["tokens"] = new_tokens
            conv["total_tokens"] += new_tokens - old_tokens
            return True

    def batch_add_messages(self, conv_id: str, messages: list) -> int:
        """Atomically add a list of (role, content, tokens) tuples.
        If conv has a context limit and the FULL batch would exceed it after drops,
        reject ALL and return -1.
        Otherwise add them all (with drops as needed).
        Returns count successfully added, or -1 on rejection/missing conv."""
        with self._lock:
            if conv_id not in self._conversations:
                return -1
            conv = self._conversations[conv_id]
            max_tokens = conv["max_tokens"]

            if max_tokens is not None:
                # Check if the entire batch alone exceeds the budget
                batch_total = sum(t for _, _, t in messages)
                if batch_total > max_tokens:
                    return -1

                # Simulate: how many existing messages get dropped?
                # We need to check if we can fit after dropping existing messages.
                # The batch cannot be partially dropped — all batch messages must fit.
                # Drop oldest existing messages as needed.
                simulated_total = conv["total_tokens"] + batch_total
                simulated_msgs = list(conv["messages"])
                while simulated_total > max_tokens and simulated_msgs:
                    oldest = simulated_msgs.pop(0)
                    simulated_total -= oldest["tokens"]

                # Actually apply the drops
                while conv["total_tokens"] + batch_total > max_tokens and conv["messages"]:
                    oldest = conv["messages"].pop(0)
                    conv["total_tokens"] -= oldest["tokens"]

            # Add all messages
            for role, content, tokens in messages:
                ts = self._next_ts()
                conv["messages"].append({"role": role, "content": content, "tokens": tokens, "ts": ts})
                conv["total_tokens"] += tokens

            self._msg_condition.notify_all()
            return len(messages)

    def wait_for_message_count(self, conv_id: str, target_count: int, timeout: float = None) -> bool:
        """Block until conv has >= target_count messages or timeout.
        Returns False on missing conv or timeout."""
        with self._lock:
            if conv_id not in self._conversations:
                return False
            if len(self._conversations[conv_id]["messages"]) >= target_count:
                return True

            deadline = None
            if timeout is not None:
                deadline = time.monotonic() + timeout

            while True:
                if conv_id not in self._conversations:
                    return False
                if len(self._conversations[conv_id]["messages"]) >= target_count:
                    return True

                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    self._msg_condition.wait(timeout=remaining)
                else:
                    self._msg_condition.wait()
