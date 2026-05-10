"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_create_single():
    queries = [["CREATE_CONVERSATION", "1", "conv_a", "alice"]]
    assert solution(queries) == ["true"]


def test_create_duplicate_returns_false():
    queries = [
        ["CREATE_CONVERSATION", "1", "conv_a", "alice"],
        ["CREATE_CONVERSATION", "2", "conv_a", "alice"],
    ]
    assert solution(queries) == ["true", "false"]


def test_create_same_id_different_user_still_false():
    """conv_id namespace is global — different user cannot reuse same id."""
    queries = [
        ["CREATE_CONVERSATION", "1", "conv_x", "alice"],
        ["CREATE_CONVERSATION", "2", "conv_x", "bob"],
    ]
    assert solution(queries) == ["true", "false"]


def test_create_multiple_distinct():
    queries = [
        ["CREATE_CONVERSATION", "1", "conv_a", "alice"],
        ["CREATE_CONVERSATION", "2", "conv_b", "bob"],
        ["CREATE_CONVERSATION", "3", "conv_c", "carol"],
    ]
    assert solution(queries) == ["true", "true", "true"]


def test_add_message_to_nonexistent_returns_empty():
    queries = [["ADD_MESSAGE", "1", "ghost", "user", "Hello", "10"]]
    assert solution(queries) == [""]


def test_add_message_returns_running_total():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["ADD_MESSAGE", "2", "c1", "user", "Hello", "10"],
        ["ADD_MESSAGE", "3", "c1", "assistant", "Hi", "15"],
        ["ADD_MESSAGE", "4", "c1", "user", "Again", "5"],
    ]
    assert solution(queries) == ["true", "10", "25", "30"]


def test_get_message_count_nonexistent_returns_empty():
    queries = [["GET_MESSAGE_COUNT", "1", "nope"]]
    assert solution(queries) == [""]


def test_get_message_count_empty_conversation_returns_zero():
    """Existing but empty conversation returns '0', not ''."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["GET_MESSAGE_COUNT", "2", "c1"],
    ]
    assert solution(queries) == ["true", "0"]


def test_get_message_count_after_adds():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["ADD_MESSAGE", "2", "c1", "user", "A", "5"],
        ["ADD_MESSAGE", "3", "c1", "assistant", "B", "8"],
        ["GET_MESSAGE_COUNT", "4", "c1"],
    ]
    assert solution(queries) == ["true", "5", "13", "2"]


def test_conversations_are_isolated():
    """Messages added to one conv do not affect another."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["CREATE_CONVERSATION", "2", "c2", "alice"],
        ["ADD_MESSAGE", "3", "c1", "user", "Hello", "20"],
        ["ADD_MESSAGE", "4", "c2", "user", "World", "30"],
        ["GET_MESSAGE_COUNT", "5", "c1"],
        ["GET_MESSAGE_COUNT", "6", "c2"],
    ]
    assert solution(queries) == ["true", "true", "20", "30", "1", "1"]


def test_add_many_messages_token_accumulation():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u1"],
        ["ADD_MESSAGE", "2", "c1", "user",      "m1", "100"],
        ["ADD_MESSAGE", "3", "c1", "assistant", "m2", "200"],
        ["ADD_MESSAGE", "4", "c1", "user",      "m3", "300"],
        ["GET_MESSAGE_COUNT", "5", "c1"],
    ]
    assert solution(queries) == ["true", "100", "300", "600", "3"]


def test_full_worked_example():
    """Matches the worked example in spec/level1.md."""
    queries = [
        ["CREATE_CONVERSATION", "1",  "conv_a", "alice"],
        ["CREATE_CONVERSATION", "2",  "conv_a", "alice"],   # dup
        ["CREATE_CONVERSATION", "3",  "conv_b", "bob"],
        ["ADD_MESSAGE",         "4",  "conv_a", "user",      "Hello!",     "10"],
        ["ADD_MESSAGE",         "5",  "conv_a", "assistant", "Hi there!",  "15"],
        ["ADD_MESSAGE",         "6",  "conv_z", "user",      "Nobody?",    "5"],  # missing
        ["GET_MESSAGE_COUNT",   "7",  "conv_a"],
        ["GET_MESSAGE_COUNT",   "8",  "conv_b"],
        ["ADD_MESSAGE",         "9",  "conv_a", "user",      "One more.",  "20"],
        ["GET_MESSAGE_COUNT",   "10", "conv_z"],                                   # missing
    ]
    assert solution(queries) == [
        "true", "false", "true",
        "10", "25", "",
        "2", "0",
        "45",
        "",
    ]


def test_role_not_validated():
    """Any role string is accepted."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["ADD_MESSAGE", "2", "c1", "system", "Instructions", "50"],
        ["ADD_MESSAGE", "3", "c1", "tool",   "Result",       "20"],
        ["GET_MESSAGE_COUNT", "4", "c1"],
    ]
    assert solution(queries) == ["true", "50", "70", "2"]


def test_large_token_values():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u1"],
        ["ADD_MESSAGE", "2", "c1", "user", "big", "1000000000"],
        ["ADD_MESSAGE", "3", "c1", "user", "big", "2000000000"],
    ]
    assert solution(queries) == ["true", "1000000000", "3000000000"]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 1 complete — commit and request Level 2.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
