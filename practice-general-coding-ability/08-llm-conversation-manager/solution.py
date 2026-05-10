"""
LLM Conversation Manager.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

Level 1: CREATE_CONVERSATION, ADD_MESSAGE, GET_MESSAGE_COUNT
Level 2: TOP_K_ACTIVE, LIST_USER_CONVERSATIONS
Level 3: SET_CONTEXT_LIMIT, ADD_MESSAGE_WITH_BUDGET
Level 4: FORK_CONVERSATION, MERGE_CONVERSATIONS
"""

from collections import deque
import copy


class Message:
    __slots__ = ("ts", "role", "content", "tokens")

    def __init__(self, ts, role, content, tokens):
        self.ts = int(ts)       # query timestamp at ADD_MESSAGE time — merge sort key
        self.role = role
        self.content = content
        self.tokens = int(tokens)


class Conversation:
    __slots__ = ("conv_id", "user_id", "messages", "total_tokens", "max_tokens")

    def __init__(self, conv_id, user_id):
        self.conv_id = conv_id
        self.user_id = user_id
        self.messages = deque()   # deque of Message; popleft() removes oldest
        self.total_tokens = 0
        self.max_tokens = None    # None = no budget


def _fifo_drop_to_fit(conv, limit):
    """Drop oldest messages from conv until total_tokens <= limit. Returns drop count."""
    dropped = 0
    while conv.total_tokens > limit:
        msg = conv.messages.popleft()
        conv.total_tokens -= msg.tokens
        dropped += 1
    return dropped


def _deep_copy_conv(source, new_conv_id):
    """Return an independent deep copy of source as a new Conversation with new_conv_id."""
    new_conv = Conversation(new_conv_id, source.user_id)
    # Deep copy each message individually (Message objects are simple value types)
    for msg in source.messages:
        new_msg = Message.__new__(Message)
        new_msg.ts = msg.ts
        new_msg.role = msg.role
        new_msg.content = msg.content
        new_msg.tokens = msg.tokens
        new_conv.messages.append(new_msg)
    new_conv.total_tokens = source.total_tokens
    new_conv.max_tokens = source.max_tokens   # int or None — both immutable, safe to copy directly
    return new_conv


def solution(queries: list[list[str]]) -> list[str]:
    convs = {}       # conv_id -> Conversation
    user_convs = {}  # user_id -> list[conv_id]  (for LIST_USER_CONVERSATIONS)
    out = []

    for q in queries:
        op = q[0]

        # ------------------------------------------------------------------ #
        #  Level 1                                                             #
        # ------------------------------------------------------------------ #

        if op == "CREATE_CONVERSATION":
            _, ts, conv_id, user_id = q
            if conv_id in convs:
                out.append("false")
            else:
                convs[conv_id] = Conversation(conv_id, user_id)
                if user_id not in user_convs:
                    user_convs[user_id] = []
                user_convs[user_id].append(conv_id)
                out.append("true")

        elif op == "ADD_MESSAGE":
            _, ts, conv_id, role, content, tokens = q
            if conv_id not in convs:
                out.append("")
            else:
                conv = convs[conv_id]
                msg = Message(ts, role, content, tokens)
                conv.messages.append(msg)
                conv.total_tokens += msg.tokens
                out.append(str(conv.total_tokens))

        elif op == "GET_MESSAGE_COUNT":
            _, ts, conv_id = q
            if conv_id not in convs:
                out.append("")
            else:
                out.append(str(len(convs[conv_id].messages)))

        # ------------------------------------------------------------------ #
        #  Level 2                                                             #
        # ------------------------------------------------------------------ #

        elif op == "TOP_K_ACTIVE":
            _, ts, k = q
            k = int(k)
            if not convs:
                out.append("")
            else:
                # Sort by message count DESC, then conv_id ASC for ties
                ranked = sorted(
                    convs.values(),
                    key=lambda c: (-len(c.messages), c.conv_id)
                )[:k]
                out.append(", ".join(f"{c.conv_id}({len(c.messages)})" for c in ranked))

        elif op == "LIST_USER_CONVERSATIONS":
            _, ts, user_id = q
            ids = user_convs.get(user_id, [])
            # Filter to only those still in convs (absorbed merges remove from convs and user_convs)
            active = sorted(cid for cid in ids if cid in convs)
            out.append(", ".join(active) if active else "")

        # ------------------------------------------------------------------ #
        #  Level 3                                                             #
        # ------------------------------------------------------------------ #

        elif op == "SET_CONTEXT_LIMIT":
            _, ts, conv_id, max_tokens = q
            if conv_id not in convs:
                out.append("")
            else:
                conv = convs[conv_id]
                conv.max_tokens = int(max_tokens)
                dropped = _fifo_drop_to_fit(conv, conv.max_tokens)
                out.append(str(dropped))

        elif op == "ADD_MESSAGE_WITH_BUDGET":
            _, ts, conv_id, role, content, tokens = q
            if conv_id not in convs:
                out.append("")
                continue
            conv = convs[conv_id]
            new_tokens = int(tokens)

            if conv.max_tokens is None:
                # No budget set — behave exactly like ADD_MESSAGE, return "0"
                msg = Message(ts, role, content, tokens)
                conv.messages.append(msg)
                conv.total_tokens += msg.tokens
                out.append("0")
            elif new_tokens > conv.max_tokens:
                # New message alone exceeds budget — reject, no state change
                out.append("")
            else:
                # Drop oldest until new message fits
                dropped = 0
                while conv.total_tokens + new_tokens > conv.max_tokens:
                    old = conv.messages.popleft()
                    conv.total_tokens -= old.tokens
                    dropped += 1
                msg = Message(ts, role, content, tokens)
                conv.messages.append(msg)
                conv.total_tokens += msg.tokens
                out.append(str(dropped))

        # ------------------------------------------------------------------ #
        #  Level 4                                                             #
        # ------------------------------------------------------------------ #

        elif op == "FORK_CONVERSATION":
            _, ts, source_conv_id, new_conv_id = q
            if source_conv_id not in convs or new_conv_id in convs:
                out.append("")
            else:
                source = convs[source_conv_id]
                new_conv = _deep_copy_conv(source, new_conv_id)
                convs[new_conv_id] = new_conv
                if new_conv.user_id not in user_convs:
                    user_convs[new_conv.user_id] = []
                user_convs[new_conv.user_id].append(new_conv_id)
                out.append("true")

        elif op == "MERGE_CONVERSATIONS":
            _, ts, surviving_id, absorbed_id = q
            if (surviving_id not in convs
                    or absorbed_id not in convs
                    or surviving_id == absorbed_id):
                out.append("")
                continue

            surviving = convs[surviving_id]
            absorbed = convs[absorbed_id]

            # Step 1: merge message lists, sort by (msg.ts ASC, origin: 0=surviving, 1=absorbed)
            tagged_surviving = [(msg.ts, 0, msg) for msg in surviving.messages]
            tagged_absorbed  = [(msg.ts, 1, msg) for msg in absorbed.messages]
            merged = sorted(tagged_surviving + tagged_absorbed, key=lambda x: (x[0], x[1]))

            # Step 2: rebuild surviving's message deque and recompute total_tokens
            surviving.messages = deque(m for _, _, m in merged)
            surviving.total_tokens = sum(m.tokens for m in surviving.messages)

            # Step 3: enforce surviving's context limit if any
            if surviving.max_tokens is not None:
                _fifo_drop_to_fit(surviving, surviving.max_tokens)

            # Step 4: delete absorbed from all data structures
            absorbed_user = absorbed.user_id
            del convs[absorbed_id]
            if absorbed_user in user_convs:
                try:
                    user_convs[absorbed_user].remove(absorbed_id)
                except ValueError:
                    pass

            out.append("true")

        else:
            raise ValueError(f"Unknown op: {op!r}")

    return out
