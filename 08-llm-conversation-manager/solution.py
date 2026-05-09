"""
LLM Conversation Manager.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

The skeleton below has the loop set up for you. You fill in the branch
bodies for each level. Delete the NotImplementedError once you start.

Level 1: CREATE_CONVERSATION, ADD_MESSAGE, GET_MESSAGE_COUNT
                                                — see spec/level1.md
Level 2: TOP_K_ACTIVE, LIST_USER_CONVERSATIONS  — see spec/level2.md
Level 3: SET_CONTEXT_LIMIT, ADD_MESSAGE_WITH_BUDGET
                                                — see spec/level3.md
Level 4: FORK_CONVERSATION, MERGE_CONVERSATIONS — see spec/level4.md
"""

from collections import deque


class Message:
    def __init__(self, ts, role, content, tokens):
        self.ts = int(ts)          # timestamp of the ADD_MESSAGE query — used for merge ordering
        self.role = role
        self.content = content
        self.tokens = int(tokens)


class Conversation:
    def __init__(self, conv_id, user_id):
        self.conv_id = conv_id
        self.user_id = user_id
        self.messages = deque()    # deque of Message objects; popleft() = oldest
        self.total_tokens = 0
        self.max_tokens = None     # None means no budget set


def solution(queries: list[list[str]]) -> list[str]:
    convs = {}        # conv_id (str) -> Conversation
    user_convs = {}   # user_id (str) -> list[conv_id]  (for LIST_USER_CONVERSATIONS)
    out = []

    for q in queries:
        op = q[0]

        # ------------------------------------------------------------------ #
        #  Level 1                                                             #
        # ------------------------------------------------------------------ #

        if op == "CREATE_CONVERSATION":
            # q is ["CREATE_CONVERSATION", <ts>, <conv_id>, <user_id>]
            _, ts, conv_id, user_id = q
            raise NotImplementedError(
                "CREATE_CONVERSATION — see spec/level1.md: "
                "create a new Conversation, add to convs and user_convs; "
                "return 'true' if new, 'false' if conv_id already exists"
            )

        elif op == "ADD_MESSAGE":
            # q is ["ADD_MESSAGE", <ts>, <conv_id>, <role>, <content>, <tokens>]
            _, ts, conv_id, role, content, tokens = q
            raise NotImplementedError(
                "ADD_MESSAGE — see spec/level1.md: "
                "append a Message to conv.messages, update conv.total_tokens; "
                "return total token count as string, or '' if conv missing"
            )

        elif op == "GET_MESSAGE_COUNT":
            # q is ["GET_MESSAGE_COUNT", <ts>, <conv_id>]
            _, ts, conv_id = q
            raise NotImplementedError(
                "GET_MESSAGE_COUNT — see spec/level1.md: "
                "return len(conv.messages) as string, or '' if conv missing"
            )

        # ------------------------------------------------------------------ #
        #  Level 2                                                             #
        # ------------------------------------------------------------------ #

        elif op == "TOP_K_ACTIVE":
            # q is ["TOP_K_ACTIVE", <ts>, <k>]
            _, ts, k = q
            # k = int(k)
            # Sort convs by message count DESC, then conv_id ASC.
            # Return top-k formatted as "conv1(50), conv2(30)".
            # Return "" if no conversations exist.
            raise NotImplementedError(
                "TOP_K_ACTIVE — see spec/level2.md: "
                "sort all convs by len(messages) DESC then conv_id ASC; "
                "return top-k formatted, '' if no convs at all"
            )

        elif op == "LIST_USER_CONVERSATIONS":
            # q is ["LIST_USER_CONVERSATIONS", <ts>, <user_id>]
            _, ts, user_id = q
            # Return alphabetically sorted conv_ids owned by user_id.
            # Return "" if user unknown or has no conversations.
            raise NotImplementedError(
                "LIST_USER_CONVERSATIONS — see spec/level2.md: "
                "look up user_convs[user_id], sort alphabetically, "
                "join with ', '; return '' if empty or unknown user"
            )

        # ------------------------------------------------------------------ #
        #  Level 3                                                             #
        # ------------------------------------------------------------------ #

        elif op == "SET_CONTEXT_LIMIT":
            # q is ["SET_CONTEXT_LIMIT", <ts>, <conv_id>, <max_tokens>]
            _, ts, conv_id, max_tokens = q
            # max_tokens = int(max_tokens)
            # Set conv.max_tokens. Then drop oldest messages (popleft) until
            # conv.total_tokens <= max_tokens. Return count dropped, or '' if missing.
            raise NotImplementedError(
                "SET_CONTEXT_LIMIT — see spec/level3.md: "
                "store conv.max_tokens = int(max_tokens); "
                "FIFO-drop oldest until total_tokens <= max_tokens; "
                "return count dropped as string, '' if conv missing"
            )

        elif op == "ADD_MESSAGE_WITH_BUDGET":
            # q is ["ADD_MESSAGE_WITH_BUDGET", <ts>, <conv_id>, <role>, <content>, <tokens>]
            _, ts, conv_id, role, content, tokens = q
            # new_tokens = int(tokens)
            # If conv missing: return "".
            # If conv has no max_tokens: behave like ADD_MESSAGE, return "0".
            # If new_tokens > max_tokens: reject (no state change), return "".
            # Otherwise: drop oldest until total_tokens + new_tokens <= max_tokens;
            #   append message; return count dropped.
            raise NotImplementedError(
                "ADD_MESSAGE_WITH_BUDGET — see spec/level3.md: "
                "reject if new_tokens > max_tokens (return ''); "
                "FIFO-drop oldest to make room; append; return drop count; "
                "if no limit set, behave like ADD_MESSAGE and return '0'"
            )

        # ------------------------------------------------------------------ #
        #  Level 4                                                             #
        # ------------------------------------------------------------------ #

        elif op == "FORK_CONVERSATION":
            # q is ["FORK_CONVERSATION", <ts>, <source_conv_id>, <new_conv_id>]
            _, ts, source_conv_id, new_conv_id = q
            # Return "" if source missing or new_conv_id already exists.
            # Create a NEW Conversation with:
            #   - same user_id as source
            #   - deep copy of source.messages (independent Message objects)
            #   - same max_tokens as source (or None)
            #   - same total_tokens as source
            # Register in convs and user_convs. Return "true".
            raise NotImplementedError(
                "FORK_CONVERSATION — see spec/level4.md: "
                "deep-copy source conv (messages, max_tokens, total_tokens, owner); "
                "register forked conv under same user; return 'true'; "
                "return '' if source missing or new_conv_id already taken"
            )

        elif op == "MERGE_CONVERSATIONS":
            # q is ["MERGE_CONVERSATIONS", <ts>, <surviving_conv>, <absorbed_conv>]
            _, ts, surviving_conv, absorbed_conv = q
            # Return "" if either missing or surviving_conv == absorbed_conv.
            # Merge steps:
            #   1. Combine message lists; sort by (msg.ts ASC, origin: 0=surviving 1=absorbed).
            #   2. Recompute surviving.total_tokens from merged list.
            #   3. If surviving has max_tokens and total > max_tokens, FIFO-drop oldest.
            #   4. Delete absorbed from convs and user_convs.
            # Return "true".
            raise NotImplementedError(
                "MERGE_CONVERSATIONS — see spec/level4.md: "
                "combine messages sorted by msg.ts (surviving first on tie); "
                "keep surviving owner + limit; drop oldest if over budget; "
                "delete absorbed; return 'true'; '' if either missing or same"
            )

        else:
            raise ValueError(f"Unknown op: {op!r}")

    return out
