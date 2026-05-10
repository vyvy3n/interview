"""
Level 2 tests — run with: python test_level2.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_top_k_no_conversations_returns_empty():
    queries = [["TOP_K_ACTIVE", "1", "3"]]
    assert solution(queries) == [""]


def test_top_k_single_conv_no_messages():
    queries = [
        ["CREATE_CONVERSATION", "1", "conv_a", "alice"],
        ["TOP_K_ACTIVE",        "2", "1"],
    ]
    assert solution(queries) == ["true", "conv_a(0)"]


def test_top_k_by_message_count_desc():
    queries = [
        ["CREATE_CONVERSATION", "1", "conv_a", "alice"],
        ["CREATE_CONVERSATION", "2", "conv_b", "alice"],
        ["CREATE_CONVERSATION", "3", "conv_c", "alice"],
        ["ADD_MESSAGE", "4", "conv_b", "user", "msg", "5"],
        ["ADD_MESSAGE", "5", "conv_b", "user", "msg", "5"],
        ["ADD_MESSAGE", "6", "conv_a", "user", "msg", "5"],
        ["TOP_K_ACTIVE", "7", "3"],
    ]
    # conv_b:2, conv_a:1, conv_c:0
    # ADD_MESSAGE returns the CALLED CONV's cumulative tokens (per-conv, not global).
    assert solution(queries) == ["true", "true", "true", "5", "10", "5", "conv_b(2), conv_a(1), conv_c(0)"]


def test_top_k_tie_broken_alphabetically():
    queries = [
        ["CREATE_CONVERSATION", "1", "zoo",   "u"],
        ["CREATE_CONVERSATION", "2", "alpha", "u"],
        ["CREATE_CONVERSATION", "3", "mid",   "u"],
        ["ADD_MESSAGE", "4", "zoo",   "user", "x", "1"],
        ["ADD_MESSAGE", "5", "alpha", "user", "x", "1"],
        ["ADD_MESSAGE", "6", "mid",   "user", "x", "1"],
        ["TOP_K_ACTIVE", "7", "3"],
    ]
    # all have 1 message — tie-break alphabetical: alpha, mid, zoo
    assert solution(queries) == ["true", "true", "true", "1", "1", "1", "alpha(1), mid(1), zoo(1)"]


def test_top_k_fewer_than_k_returns_all():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["CREATE_CONVERSATION", "2", "c2", "u"],
        ["TOP_K_ACTIVE", "3", "10"],
    ]
    assert solution(queries) == ["true", "true", "c1(0), c2(0)"]


def test_top_k_k_equals_one():
    queries = [
        ["CREATE_CONVERSATION", "1", "conv_a", "alice"],
        ["CREATE_CONVERSATION", "2", "conv_b", "alice"],
        ["ADD_MESSAGE", "3", "conv_a", "user", "x", "5"],
        ["ADD_MESSAGE", "4", "conv_a", "user", "x", "5"],
        ["ADD_MESSAGE", "5", "conv_b", "user", "x", "5"],
        ["TOP_K_ACTIVE", "6", "1"],
    ]
    # ADD_MESSAGE returns the CALLED CONV's cumulative tokens.
    # conv_a: 5 → 10. conv_b: 5.
    assert solution(queries) == ["true", "true", "5", "10", "5", "conv_a(2)"]


def test_list_user_conversations_single_user():
    queries = [
        ["CREATE_CONVERSATION", "1", "conv_b", "alice"],
        ["CREATE_CONVERSATION", "2", "conv_a", "alice"],
        ["LIST_USER_CONVERSATIONS", "3", "alice"],
    ]
    # alphabetical: conv_a, conv_b
    assert solution(queries) == ["true", "true", "conv_a, conv_b"]


def test_list_user_conversations_unknown_user():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["LIST_USER_CONVERSATIONS", "2", "ghost"],
    ]
    assert solution(queries) == ["true", ""]


def test_list_user_conversations_multiple_users():
    queries = [
        ["CREATE_CONVERSATION", "1", "c_b", "alice"],
        ["CREATE_CONVERSATION", "2", "c_a", "alice"],
        ["CREATE_CONVERSATION", "3", "d_1", "bob"],
        ["LIST_USER_CONVERSATIONS", "4", "alice"],
        ["LIST_USER_CONVERSATIONS", "5", "bob"],
    ]
    assert solution(queries) == ["true", "true", "true", "c_a, c_b", "d_1"]


def test_list_user_conversations_empty_for_no_convs():
    """User with no conversations returns ''."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["LIST_USER_CONVERSATIONS", "2", "bob"],
    ]
    assert solution(queries) == ["true", ""]


def test_full_worked_example():
    """Matches the worked example in spec/level2.md."""
    queries = [
        ["CREATE_CONVERSATION",     "1",  "conv_b", "alice"],
        ["CREATE_CONVERSATION",     "2",  "conv_a", "alice"],
        ["CREATE_CONVERSATION",     "3",  "conv_c", "bob"],
        ["ADD_MESSAGE",             "4",  "conv_a", "user",      "Hi",   "5"],
        ["ADD_MESSAGE",             "5",  "conv_a", "assistant", "Hey",  "8"],
        ["ADD_MESSAGE",             "6",  "conv_b", "user",      "Yo",   "3"],
        ["TOP_K_ACTIVE",            "7",  "2"],
        ["TOP_K_ACTIVE",            "8",  "5"],
        ["LIST_USER_CONVERSATIONS", "9",  "alice"],
        ["LIST_USER_CONVERSATIONS", "10", "bob"],
        ["LIST_USER_CONVERSATIONS", "11", "carol"],
    ]
    assert solution(queries) == [
        "true", "true", "true",
        "5", "13", "3",
        "conv_a(2), conv_b(1)",
        "conv_a(2), conv_b(1), conv_c(0)",
        "conv_a, conv_b",
        "conv_c",
        "",
    ]


def test_top_k_includes_zero_message_convs():
    """Zero-message conversations are NOT excluded from TOP_K_ACTIVE."""
    queries = [
        ["CREATE_CONVERSATION", "1", "empty1", "u"],
        ["CREATE_CONVERSATION", "2", "empty2", "u"],
        ["TOP_K_ACTIVE", "3", "5"],
    ]
    assert solution(queries) == ["true", "true", "empty1(0), empty2(0)"]


def test_top_k_after_more_messages_added():
    """Rankings update dynamically as messages are added."""
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "u"],
        ["CREATE_CONVERSATION", "2", "b", "u"],
        ["TOP_K_ACTIVE", "3", "2"],
        ["ADD_MESSAGE", "4", "b", "user", "x", "1"],
        ["ADD_MESSAGE", "5", "b", "user", "x", "1"],
        ["TOP_K_ACTIVE", "6", "2"],
    ]
    # After setup: both 0. After adds: b=2, a=0.
    assert solution(queries) == ["true", "true", "a(0), b(0)", "1", "2", "b(2), a(0)"]


# ----- Test runner -----


def run_all():
    tests = [(name, fn) for name, fn in globals().items()
             if name.startswith("test_") and callable(fn)]
    passed = 0
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  \033[32m✓\033[0m {name}")
            passed += 1
        except NotImplementedError as e:
            print(f"  \033[33m○\033[0m {name} — not implemented")
            failed.append((name, str(e)))
        except AssertionError:
            tb = traceback.format_exc(limit=2)
            print(f"  \033[31m✗\033[0m {name}")
            print("    " + "\n    ".join(tb.splitlines()[-4:]))
            failed.append((name, "assertion"))
        except Exception as e:
            tb = traceback.format_exc(limit=2)
            print(f"  \033[31m✗\033[0m {name} — {type(e).__name__}: {e}")
            print("    " + "\n    ".join(tb.splitlines()[-4:]))
            failed.append((name, f"{type(e).__name__}"))
    total = len(tests)
    print()
    if not failed:
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 2 complete — commit and request Level 3.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
