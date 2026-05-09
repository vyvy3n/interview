"""
Level 4 tests — run with: python test_level4.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_fork_basic():
    queries = [
        ["CREATE_CONVERSATION", "1", "main",   "alice"],
        ["ADD_MESSAGE",         "2", "main",   "user", "Hello", "50"],
        ["FORK_CONVERSATION",   "3", "main",   "branch"],
        ["GET_MESSAGE_COUNT",   "4", "branch"],
    ]
    assert solution(queries) == ["true", "50", "true", "1"]


def test_fork_missing_source_returns_empty():
    queries = [["FORK_CONVERSATION", "1", "ghost", "new"]]
    assert solution(queries) == [""]


def test_fork_new_id_already_exists_returns_empty():
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "alice"],
        ["CREATE_CONVERSATION", "2", "b", "alice"],
        ["FORK_CONVERSATION",   "3", "a", "b"],    # b already exists
    ]
    assert solution(queries) == ["true", "true", ""]


def test_fork_creates_independent_state():
    """Modifications to fork do not affect parent, and vice versa."""
    queries = [
        ["CREATE_CONVERSATION", "1", "main",   "alice"],
        ["ADD_MESSAGE",         "2", "main",   "user", "Original", "30"],
        ["FORK_CONVERSATION",   "3", "main",   "fork1"],
        # Add to fork — parent should not see it
        ["ADD_MESSAGE",         "4", "fork1",  "assistant", "Fork reply", "20"],
        # Add to parent — fork should not see it
        ["ADD_MESSAGE",         "5", "main",   "user", "Parent only", "25"],
        ["GET_MESSAGE_COUNT",   "6", "main"],   # 2
        ["GET_MESSAGE_COUNT",   "7", "fork1"],  # 2
    ]
    assert solution(queries) == ["true", "30", "true", "50", "55", "2", "2"]


def test_fork_inherits_context_limit():
    """Fork starts with same max_tokens as source."""
    queries = [
        ["CREATE_CONVERSATION",     "1", "main",  "alice"],
        ["ADD_MESSAGE",             "2", "main",  "user", "msg", "80"],
        ["SET_CONTEXT_LIMIT",       "3", "main",  "100"],
        ["FORK_CONVERSATION",       "4", "main",  "fork1"],
        # Add message that would exceed limit — fork should enforce it
        ["ADD_MESSAGE_WITH_BUDGET", "5", "fork1", "user", "new", "50"],
        # 80 + 50 = 130 > 100 → drop oldest → 0 + 50 = 50 ≤ 100 → 1 dropped
        ["GET_MESSAGE_COUNT",       "6", "fork1"],
        # main is unaffected
        ["GET_MESSAGE_COUNT",       "7", "main"],
    ]
    assert solution(queries) == ["true", "80", "0", "true", "1", "1", "1"]


def test_fork_context_limit_is_independent():
    """Changing limit on fork does not affect parent."""
    queries = [
        ["CREATE_CONVERSATION", "1", "main",  "alice"],
        ["ADD_MESSAGE",         "2", "main",  "user", "msg", "80"],
        ["SET_CONTEXT_LIMIT",   "3", "main",  "200"],
        ["FORK_CONVERSATION",   "4", "main",  "fork1"],
        ["SET_CONTEXT_LIMIT",   "5", "fork1", "50"],  # tightens fork's limit; drops fork's msg
        ["GET_MESSAGE_COUNT",   "6", "fork1"],         # 0 msgs after drop
        ["GET_MESSAGE_COUNT",   "7", "main"],          # still 1 msg
    ]
    assert solution(queries) == ["true", "80", "0", "true", "1", "0", "1"]


def test_merge_basic():
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "alice"],
        ["CREATE_CONVERSATION", "2", "b", "alice"],
        ["ADD_MESSAGE",         "3", "a", "user", "from_a", "10"],
        ["ADD_MESSAGE",         "4", "b", "user", "from_b", "20"],
        ["MERGE_CONVERSATIONS", "5", "a", "b"],
        ["GET_MESSAGE_COUNT",   "6", "a"],
        ["GET_MESSAGE_COUNT",   "7", "b"],   # b is gone
    ]
    assert solution(queries) == ["true", "true", "10", "20", "true", "2", ""]


def test_merge_missing_surviving_returns_empty():
    queries = [
        ["CREATE_CONVERSATION", "1", "b", "alice"],
        ["MERGE_CONVERSATIONS", "2", "ghost", "b"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_missing_absorbed_returns_empty():
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "alice"],
        ["MERGE_CONVERSATIONS", "2", "a", "ghost"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_same_conv_returns_empty():
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "alice"],
        ["MERGE_CONVERSATIONS", "2", "a", "a"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_interleaves_by_timestamp():
    """Messages must be sorted by their original ADD_MESSAGE timestamp."""
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "alice"],
        ["CREATE_CONVERSATION", "2", "b", "alice"],
        ["ADD_MESSAGE",         "3", "a", "user", "a_first",  "10"],
        ["ADD_MESSAGE",         "5", "b", "user", "b_second", "20"],
        ["ADD_MESSAGE",         "7", "a", "user", "a_third",  "30"],
        ["ADD_MESSAGE",         "9", "b", "user", "b_fourth", "40"],
        ["MERGE_CONVERSATIONS", "10", "a", "b"],
        # merged order by ts: ts=3(a), ts=5(b), ts=7(a), ts=9(b) → 4 messages
        ["GET_MESSAGE_COUNT",   "11", "a"],
    ]
    assert solution(queries) == ["true", "true", "10", "20", "30", "40", "true", "4"]


def test_merge_tie_surviving_before_absorbed():
    """When two messages share a timestamp, surviving's message comes first."""
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "alice"],
        ["CREATE_CONVERSATION", "2", "b", "alice"],
        ["ADD_MESSAGE",         "3", "a", "user", "from_a_ts3", "10"],
        ["ADD_MESSAGE",         "3", "b", "user", "from_b_ts3", "20"],  # same ts=3
        ["MERGE_CONVERSATIONS", "4", "a", "b"],
        # a's message at ts=3 comes before b's at ts=3
        ["GET_MESSAGE_COUNT",   "5", "a"],
    ]
    assert solution(queries) == ["true", "true", "10", "20", "true", "2"]


def test_merge_absorbed_is_deleted_from_reports():
    queries = [
        ["CREATE_CONVERSATION",     "1", "a",    "alice"],
        ["CREATE_CONVERSATION",     "2", "b",    "bob"],
        ["ADD_MESSAGE",             "3", "b",    "user", "msg", "10"],
        ["MERGE_CONVERSATIONS",     "4", "a",    "b"],
        ["LIST_USER_CONVERSATIONS", "5", "bob"],   # b is gone
        ["TOP_K_ACTIVE",            "6", "5"],     # only a should appear
    ]
    assert solution(queries) == ["true", "true", "10", "true", "", "a(1)"]


def test_merge_with_context_limit_truncates():
    """After merge, surviving's context limit is enforced by dropping oldest."""
    queries = [
        ["CREATE_CONVERSATION", "1",  "a", "alice"],
        ["CREATE_CONVERSATION", "2",  "b", "alice"],
        ["ADD_MESSAGE",         "3",  "a", "user", "a1", "60"],
        ["ADD_MESSAGE",         "5",  "b", "user", "b1", "60"],
        ["ADD_MESSAGE",         "7",  "a", "user", "a2", "60"],
        ["SET_CONTEXT_LIMIT",   "8",  "a", "100"],
        # after limit: a has 60+60=120>100 → drop a1(ts=3) → 60≤100 → 1 dropped; a now has [a2]
        ["MERGE_CONVERSATIONS", "9",  "a", "b"],
        # surviving a has [a2(ts=7,60)]; absorbed b has [b1(ts=5,60)]
        # merged sorted by ts: [b1(ts=5,60), a2(ts=7,60)] → total=120>100
        # drop b1(ts=5) → total=60≤100 → done
        ["GET_MESSAGE_COUNT",   "10", "a"],   # 1 message remains
    ]
    assert solution(queries) == ["true", "true", "60", "60", "60", "1", "true", "1"]


def test_fork_absorbed_conv_does_not_exist():
    """Cannot fork a conversation that has been absorbed in a merge."""
    queries = [
        ["CREATE_CONVERSATION", "1", "a", "alice"],
        ["CREATE_CONVERSATION", "2", "b", "alice"],
        ["MERGE_CONVERSATIONS", "3", "a", "b"],
        ["FORK_CONVERSATION",   "4", "b", "c"],   # b is gone
    ]
    assert solution(queries) == ["true", "true", "true", ""]


def test_merge_surviving_keeps_own_owner():
    """surviving_conv retains its original owner, not absorbed's."""
    queries = [
        ["CREATE_CONVERSATION",     "1", "a", "alice"],
        ["CREATE_CONVERSATION",     "2", "b", "bob"],
        ["MERGE_CONVERSATIONS",     "3", "a", "b"],
        ["LIST_USER_CONVERSATIONS", "4", "alice"],
        ["LIST_USER_CONVERSATIONS", "5", "bob"],
    ]
    assert solution(queries) == ["true", "true", "true", "a", ""]


def test_full_worked_example():
    """Matches the worked example in spec/level4.md."""
    queries = [
        ["CREATE_CONVERSATION",     "1",  "main",   "alice"],
        ["ADD_MESSAGE",             "2",  "main",   "user",      "Hello",     "50"],
        ["ADD_MESSAGE",             "3",  "main",   "assistant", "Hi back",   "60"],
        ["FORK_CONVERSATION",       "4",  "main",   "branch"],
        ["ADD_MESSAGE",             "5",  "main",   "user",      "Continue",  "40"],
        ["ADD_MESSAGE",             "6",  "branch", "assistant", "Alternate", "45"],
        ["GET_MESSAGE_COUNT",       "7",  "main"],
        ["GET_MESSAGE_COUNT",       "8",  "branch"],
        ["MERGE_CONVERSATIONS",     "9",  "main",   "branch"],
        ["GET_MESSAGE_COUNT",       "10", "main"],
        ["GET_MESSAGE_COUNT",       "11", "branch"],
        ["SET_CONTEXT_LIMIT",       "12", "main",   "120"],
        ["FORK_CONVERSATION",       "13", "main",   "trimmed"],
        ["ADD_MESSAGE_WITH_BUDGET", "14", "trimmed","user",      "Extra",     "30"],
        ["GET_MESSAGE_COUNT",       "15", "main"],
        ["GET_MESSAGE_COUNT",       "16", "trimmed"],
    ]
    assert solution(queries) == [
        "true",   # create main
        "50",     # add Hello ts=2
        "110",    # add Hi back ts=3
        "true",   # fork main→branch
        "150",    # add Continue to main ts=5
        "155",    # add Alternate to branch ts=6
        "3",      # main: 3 msgs
        "3",      # branch: 3 msgs
        "true",   # merge main←branch; 6 msgs total, no limit
        "6",      # main: 6 msgs
        "",       # branch gone
        "4",      # set limit 120 on main (total 305); drop 4 msgs
        "true",   # fork main→trimmed (2 msgs, limit=120)
        "0",      # budget-add 30 to trimmed: 85+30=115≤120 → 0 dropped
        "2",      # main still 2 msgs (fork is independent)
        "3",      # trimmed: 3 msgs
    ]


def test_multiple_forks_all_independent():
    queries = [
        ["CREATE_CONVERSATION", "1", "src",    "u"],
        ["ADD_MESSAGE",         "2", "src",    "user", "base", "10"],
        ["FORK_CONVERSATION",   "3", "src",    "f1"],
        ["FORK_CONVERSATION",   "4", "src",    "f2"],
        ["ADD_MESSAGE",         "5", "f1",     "user", "f1_only", "20"],
        ["ADD_MESSAGE",         "6", "f2",     "user", "f2_only", "30"],
        ["GET_MESSAGE_COUNT",   "7", "src"],   # 1 — unaffected
        ["GET_MESSAGE_COUNT",   "8", "f1"],    # 2
        ["GET_MESSAGE_COUNT",   "9", "f2"],    # 2
    ]
    assert solution(queries) == ["true", "10", "true", "true", "30", "40", "1", "2", "2"]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 4 complete — congratulations!")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
