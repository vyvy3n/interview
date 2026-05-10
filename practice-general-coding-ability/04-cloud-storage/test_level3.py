"""
Level 3 tests — run with: python test_level3.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_share_basic():
    queries = [
        ["CREATE_USER",      "1", "alice", "1000"],
        ["CREATE_USER",      "2", "bob",   "500"],
        ["UPLOAD",           "3", "alice", "doc", "200"],
        ["SHARE",            "4", "alice", "doc", "bob"],
        ["LIST_SHARED_WITH", "5", "bob"],
    ]
    assert solution(queries) == ["true", "true", "200", "true", "alice:doc"]


def test_share_does_not_affect_quotas():
    # sharing a file doesn't change alice's or bob's used bytes
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["UPLOAD",      "3", "alice", "doc", "400"],
        ["SHARE",       "4", "alice", "doc", "bob"],
        ["GET_USAGE",   "5", "alice"],
        ["GET_USAGE",   "6", "bob"],
    ]
    assert solution(queries) == ["true", "true", "400", "true", "400/1000", "0/500"]


def test_share_to_multiple_recipients():
    queries = [
        ["CREATE_USER",      "1", "alice", "1000"],
        ["CREATE_USER",      "2", "bob",   "500"],
        ["CREATE_USER",      "3", "carol", "500"],
        ["UPLOAD",           "4", "alice", "doc", "200"],
        ["SHARE",            "5", "alice", "doc", "bob"],
        ["SHARE",            "6", "alice", "doc", "carol"],
        ["LIST_SHARED_WITH", "7", "bob"],
        ["LIST_SHARED_WITH", "8", "carol"],
    ]
    assert solution(queries) == [
        "true", "true", "true", "200",
        "true", "true",
        "alice:doc",
        "alice:doc",
    ]


def test_share_self_rejected():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["UPLOAD",      "2", "alice", "doc", "200"],
        ["SHARE",       "3", "alice", "doc", "alice"],
    ]
    assert solution(queries) == ["true", "200", ""]


def test_share_duplicate_rejected():
    queries = [
        ["CREATE_USER",      "1", "alice", "1000"],
        ["CREATE_USER",      "2", "bob",   "500"],
        ["UPLOAD",           "3", "alice", "doc", "200"],
        ["SHARE",            "4", "alice", "doc", "bob"],
        ["SHARE",            "5", "alice", "doc", "bob"],  # dup
        ["LIST_SHARED_WITH", "6", "bob"],
    ]
    assert solution(queries) == ["true", "true", "200", "true", "", "alice:doc"]


def test_share_missing_owner_rejected():
    queries = [
        ["CREATE_USER", "1", "bob", "500"],
        ["SHARE",       "2", "ghost", "doc", "bob"],
    ]
    assert solution(queries) == ["true", ""]


def test_share_missing_file_rejected():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["SHARE",       "3", "alice", "nonexistent", "bob"],
    ]
    assert solution(queries) == ["true", "true", ""]


def test_share_missing_recipient_rejected():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["UPLOAD",      "2", "alice", "doc", "200"],
        ["SHARE",       "3", "alice", "doc", "ghost"],
    ]
    assert solution(queries) == ["true", "200", ""]


def test_unshare_basic():
    queries = [
        ["CREATE_USER",      "1", "alice", "1000"],
        ["CREATE_USER",      "2", "bob",   "500"],
        ["UPLOAD",           "3", "alice", "doc", "200"],
        ["SHARE",            "4", "alice", "doc", "bob"],
        ["UNSHARE",          "5", "alice", "doc", "bob"],
        ["LIST_SHARED_WITH", "6", "bob"],
    ]
    assert solution(queries) == ["true", "true", "200", "true", "true", ""]


def test_unshare_nonexistent_returns_empty():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["UPLOAD",      "3", "alice", "doc", "200"],
        ["UNSHARE",     "4", "alice", "doc", "bob"],  # was never shared
    ]
    assert solution(queries) == ["true", "true", "200", ""]


def test_delete_cascades_all_shares():
    queries = [
        ["CREATE_USER",      "1", "alice", "1000"],
        ["CREATE_USER",      "2", "bob",   "500"],
        ["CREATE_USER",      "3", "carol", "500"],
        ["UPLOAD",           "4", "alice", "doc", "200"],
        ["SHARE",            "5", "alice", "doc", "bob"],
        ["SHARE",            "6", "alice", "doc", "carol"],
        ["DELETE",           "7", "alice", "doc"],
        ["LIST_SHARED_WITH", "8", "bob"],
        ["LIST_SHARED_WITH", "9", "carol"],
    ]
    # delete should cascade to both bob and carol
    assert solution(queries) == [
        "true", "true", "true", "200",
        "true", "true",
        "true",
        "",  # bob — share revoked
        "",  # carol — share revoked
    ]


def test_list_shared_with_sorted_owner_then_file():
    queries = [
        ["CREATE_USER",      "1", "alice", "1000"],
        ["CREATE_USER",      "2", "bob",   "1000"],
        ["CREATE_USER",      "3", "carol", "500"],
        ["UPLOAD",           "4", "alice", "z_file", "100"],
        ["UPLOAD",           "5", "alice", "a_file", "100"],
        ["UPLOAD",           "6", "bob",   "m_file", "100"],
        ["SHARE",            "7", "bob",   "m_file", "carol"],
        ["SHARE",            "8", "alice", "z_file", "carol"],
        ["SHARE",            "9", "alice", "a_file", "carol"],
        ["LIST_SHARED_WITH", "10","carol"],
    ]
    # sorted by owner ASC (alice < bob), then file_id ASC within owner
    # UPLOAD returns alice's CUMULATIVE used bytes per L1 spec.
    assert solution(queries) == [
        "true", "true", "true",
        "100", "200", "100",
        "true", "true", "true",
        "alice:a_file, alice:z_file, bob:m_file",
    ]


def test_list_shared_with_nothing_returns_empty():
    queries = [
        ["CREATE_USER",      "1", "alice", "1000"],
        ["LIST_SHARED_WITH", "2", "alice"],
    ]
    assert solution(queries) == ["true", ""]


def test_worked_example_from_spec():
    queries = [
        ["CREATE_USER",      "1",  "alice", "1000"],
        ["CREATE_USER",      "2",  "bob",   "500"],
        ["CREATE_USER",      "3",  "carol", "500"],
        ["UPLOAD",           "4",  "alice", "doc",   "200"],
        ["UPLOAD",           "5",  "alice", "photo", "100"],
        ["SHARE",            "6",  "alice", "doc",   "bob"],
        ["SHARE",            "7",  "alice", "doc",   "carol"],
        ["SHARE",            "8",  "alice", "photo", "bob"],
        ["SHARE",            "9",  "alice", "doc",   "bob"],   # dup
        ["SHARE",            "10", "alice", "doc",   "alice"], # self
        ["LIST_SHARED_WITH", "11", "bob"],
        ["LIST_SHARED_WITH", "12", "carol"],
        ["UNSHARE",          "13", "alice", "doc",   "bob"],
        ["LIST_SHARED_WITH", "14", "bob"],
        ["DELETE",           "15", "alice", "photo"],
        ["LIST_SHARED_WITH", "16", "bob"],
    ]
    # UPLOAD returns alice's CUMULATIVE used bytes per L1 spec.
    # alice: doc=200 → photo adds 100 → cumulative 300.
    assert solution(queries) == [
        "true", "true", "true", "200", "300",
        "true", "true", "true", "", "",
        "alice:doc, alice:photo",
        "alice:doc",
        "true",
        "alice:photo",
        "true",
        "",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 3 complete — move to Level 4.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
