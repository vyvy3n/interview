"""
Level 3 tests — run with: python test_level3.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_set_context_limit_no_drop_needed():
    """Limit is larger than current total — zero messages dropped."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["ADD_MESSAGE", "2", "c1", "user", "Hello", "50"],
        ["SET_CONTEXT_LIMIT", "3", "c1", "200"],
    ]
    assert solution(queries) == ["true", "50", "0"]


def test_set_context_limit_drops_single_oldest():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["ADD_MESSAGE", "2", "c1", "user",      "First",  "100"],
        ["ADD_MESSAGE", "3", "c1", "assistant", "Second", "100"],
        ["SET_CONTEXT_LIMIT", "4", "c1", "150"],  # total=200 > 150 → drop First (100) → 100 ≤ 150
    ]
    assert solution(queries) == ["true", "100", "200", "1"]


def test_set_context_limit_drops_multiple_oldest():
    """Must keep dropping until it fits, not just once."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["ADD_MESSAGE", "2", "c1", "user",      "m1", "100"],
        ["ADD_MESSAGE", "3", "c1", "assistant", "m2", "100"],
        ["ADD_MESSAGE", "4", "c1", "user",      "m3", "100"],
        ["ADD_MESSAGE", "5", "c1", "assistant", "m4", "100"],
        ["SET_CONTEXT_LIMIT", "6", "c1", "150"],
        # total=400 > 150; drop m1(100)→300>150; drop m2(100)→200>150; drop m3(100)→100≤150 → 3 dropped
        ["GET_MESSAGE_COUNT", "7", "c1"],
    ]
    assert solution(queries) == ["true", "100", "200", "300", "400", "3", "1"]


def test_set_context_limit_missing_conv():
    queries = [["SET_CONTEXT_LIMIT", "1", "ghost", "100"]]
    assert solution(queries) == [""]


def test_set_context_limit_exact_boundary_no_drop():
    """Limit equals current total — nothing dropped."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["ADD_MESSAGE", "2", "c1", "user", "msg", "100"],
        ["SET_CONTEXT_LIMIT", "3", "c1", "100"],
    ]
    assert solution(queries) == ["true", "100", "0"]


def test_add_message_with_budget_no_limit_set():
    """Without SET_CONTEXT_LIMIT, behaves like ADD_MESSAGE and returns '0'."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "alice"],
        ["ADD_MESSAGE_WITH_BUDGET", "2", "c1", "user", "Hello", "999"],
    ]
    assert solution(queries) == ["true", "0"]


def test_add_message_with_budget_fits_no_truncation():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["SET_CONTEXT_LIMIT", "2", "c1", "200"],
        ["ADD_MESSAGE_WITH_BUDGET", "3", "c1", "user", "Hi", "80"],
    ]
    assert solution(queries) == ["true", "0", "0"]


def test_add_message_with_budget_drops_to_make_room():
    """Drop one message to fit the new one."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["ADD_MESSAGE", "2", "c1", "user", "old1", "100"],
        ["ADD_MESSAGE", "3", "c1", "user", "old2", "100"],
        ["SET_CONTEXT_LIMIT", "4", "c1", "250"],
        # total=200; add 100 → 300 > 250 → drop old1(100) → 100; 100+100=200 ≤ 250 → add
        ["ADD_MESSAGE_WITH_BUDGET", "5", "c1", "user", "new", "100"],
        ["GET_MESSAGE_COUNT", "6", "c1"],
    ]
    assert solution(queries) == ["true", "100", "200", "0", "1", "2"]


def test_add_message_with_budget_drops_multiple():
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["ADD_MESSAGE", "2", "c1", "user", "m1", "80"],
        ["ADD_MESSAGE", "3", "c1", "user", "m2", "80"],
        ["ADD_MESSAGE", "4", "c1", "user", "m3", "80"],
        ["SET_CONTEXT_LIMIT", "5", "c1", "100"],
        # after limit: 240>100 → drop m1(80)→160>100 → drop m2(80)→80≤100 → 2 dropped (from SET_CONTEXT_LIMIT)
        # now total=80; add 50 → 80+50=130 > 100 → drop m3(80) → 0; 0+50=50≤100 → add
        ["ADD_MESSAGE_WITH_BUDGET", "6", "c1", "user", "new", "50"],
        ["GET_MESSAGE_COUNT", "7", "c1"],
    ]
    assert solution(queries) == ["true", "80", "160", "240", "2", "1", "1"]


def test_add_message_with_budget_rejection_too_big():
    """New message alone exceeds max_tokens — reject, no state change."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["ADD_MESSAGE", "2", "c1", "user", "existing", "50"],
        ["SET_CONTEXT_LIMIT", "3", "c1", "100"],
        ["ADD_MESSAGE_WITH_BUDGET", "4", "c1", "user", "huge", "200"],  # 200 > 100 → reject
        ["GET_MESSAGE_COUNT", "5", "c1"],  # still 1 message
    ]
    assert solution(queries) == ["true", "50", "0", "", "1"]


def test_add_message_with_budget_rejection_no_drop_happened():
    """Rejection must leave state completely unchanged."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["ADD_MESSAGE", "2", "c1", "user", "keep1", "40"],
        ["ADD_MESSAGE", "3", "c1", "user", "keep2", "40"],
        ["SET_CONTEXT_LIMIT", "4", "c1", "100"],
        # total=80; new=200 > 100 → reject → state unchanged
        ["ADD_MESSAGE_WITH_BUDGET", "5", "c1", "user", "too_big", "200"],
        # Verify both old messages still there
        ["GET_MESSAGE_COUNT", "6", "c1"],
    ]
    assert solution(queries) == ["true", "40", "80", "0", "", "2"]


def test_add_message_with_budget_missing_conv():
    queries = [["ADD_MESSAGE_WITH_BUDGET", "1", "ghost", "user", "hi", "10"]]
    assert solution(queries) == [""]


def test_add_message_l1_bypasses_budget():
    """L1 ADD_MESSAGE does NOT enforce the context limit."""
    queries = [
        ["CREATE_CONVERSATION", "1", "c1", "u"],
        ["SET_CONTEXT_LIMIT", "2", "c1", "50"],
        ["ADD_MESSAGE", "3", "c1", "user", "big", "9999"],  # bypasses limit
        ["GET_MESSAGE_COUNT", "4", "c1"],
    ]
    assert solution(queries) == ["true", "0", "9999", "1"]


def test_full_worked_example():
    """Matches the worked example in spec/level3.md."""
    queries = [
        ["CREATE_CONVERSATION",       "1",  "chat1", "alice"],
        ["ADD_MESSAGE",               "2",  "chat1", "user",      "First",   "100"],
        ["ADD_MESSAGE",               "3",  "chat1", "assistant", "Second",  "100"],
        ["ADD_MESSAGE",               "4",  "chat1", "user",      "Third",   "100"],
        ["SET_CONTEXT_LIMIT",         "5",  "chat1", "250"],
        ["ADD_MESSAGE_WITH_BUDGET",   "6",  "chat1", "user",      "Fourth",  "100"],
        ["ADD_MESSAGE_WITH_BUDGET",   "7",  "chat1", "user",      "TooBig",  "999"],
        ["GET_MESSAGE_COUNT",         "8",  "chat1"],
        ["ADD_MESSAGE",               "9",  "chat1", "user",      "Raw",     "500"],
        ["GET_MESSAGE_COUNT",         "10", "chat1"],
        ["SET_CONTEXT_LIMIT",         "11", "chat1", "50"],
        ["GET_MESSAGE_COUNT",         "12", "chat1"],
    ]
    assert solution(queries) == [
        "true",   # create
        "100",    # add first
        "200",    # add second
        "300",    # add third
        "1",      # set limit 250 → drop first → 1 dropped
        "1",      # budget add → drop second → 1 dropped
        "",       # 999 > 250 → reject
        "2",      # still 2 msgs (Third + Fourth)
        "700",    # L1 add bypasses limit
        "3",      # 3 msgs
        "3",      # set limit 50 → drop all 3 (100+500+100=700 → need ≤50 → drop all)
        "0",      # 0 msgs remain
    ]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 3 complete — commit and request Level 4.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
