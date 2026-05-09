"""
Level 2 tests — run with: python test_level2.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_get_usage_basic():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["UPLOAD",      "2", "alice", "doc", "300"],
        ["GET_USAGE",   "3", "alice"],
    ]
    assert solution(queries) == ["true", "300", "300/1000"]


def test_get_usage_zero_used():
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["GET_USAGE",   "2", "alice"],
    ]
    assert solution(queries) == ["true", "0/500"]


def test_get_usage_after_delete():
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["UPLOAD",      "2", "alice", "doc", "300"],
        ["DELETE",      "3", "alice", "doc"],
        ["GET_USAGE",   "4", "alice"],
    ]
    assert solution(queries) == ["true", "300", "true", "0/500"]


def test_get_usage_nonexistent_user():
    queries = [["GET_USAGE", "1", "ghost"]]
    assert solution(queries) == [""]


def test_top_k_basic_ordering():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["CREATE_USER", "3", "carol", "800"],
        ["UPLOAD",      "4", "alice", "doc",   "600"],
        ["UPLOAD",      "5", "bob",   "img",   "400"],
        ["UPLOAD",      "6", "carol", "video", "200"],
        ["TOP_K_USERS", "7", "3"],
    ]
    # alice=600, bob=400, carol=200 → alice, bob, carol
    assert solution(queries) == [
        "true", "true", "true", "600", "400", "200",
        "alice(600/1000), bob(400/500), carol(200/800)",
    ]


def test_top_k_tie_broken_alphabetically():
    queries = [
        ["CREATE_USER", "1", "zara",  "500"],
        ["CREATE_USER", "2", "alice", "500"],
        ["CREATE_USER", "3", "bob",   "500"],
        ["UPLOAD",      "4", "zara",  "doc", "200"],
        ["UPLOAD",      "5", "alice", "doc", "200"],
        ["UPLOAD",      "6", "bob",   "doc", "200"],
        ["TOP_K_USERS", "7", "3"],
    ]
    # all have 200 used → sort alphabetically: alice, bob, zara
    assert solution(queries) == [
        "true", "true", "true", "200", "200", "200",
        "alice(200/500), bob(200/500), zara(200/500)",
    ]


def test_top_k_fewer_than_k_users():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["UPLOAD",      "3", "alice", "doc", "300"],
        ["TOP_K_USERS", "4", "10"],
    ]
    # only 2 users; return both
    assert solution(queries) == ["true", "true", "300", "alice(300/1000), bob(0/500)"]


def test_top_k_includes_zero_usage_users():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["CREATE_USER", "3", "carol", "200"],
        ["UPLOAD",      "4", "alice", "doc", "700"],
        ["TOP_K_USERS", "5", "3"],
    ]
    # alice=700, bob=0, carol=0; bob and carol tie at 0 → bob < carol alphabetically
    assert solution(queries) == [
        "true", "true", "true", "700",
        "alice(700/1000), bob(0/500), carol(0/200)",
    ]


def test_top_k_1_returns_single_user():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["UPLOAD",      "3", "alice", "doc", "800"],
        ["UPLOAD",      "4", "bob",   "img", "400"],
        ["TOP_K_USERS", "5", "1"],
    ]
    assert solution(queries) == ["true", "true", "800", "400", "alice(800/1000)"]


def test_top_k_no_users_returns_empty():
    queries = [["TOP_K_USERS", "1", "5"]]
    assert solution(queries) == [""]


def test_top_k_after_delete_updates_ranking():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["UPLOAD",      "3", "alice", "doc", "300"],
        ["UPLOAD",      "4", "bob",   "img", "400"],
        ["TOP_K_USERS", "5", "2"],
        ["DELETE",      "6", "bob",   "img"],
        ["TOP_K_USERS", "7", "2"],
    ]
    # before delete: bob=400, alice=300 → bob, alice
    # after delete: alice=300, bob=0 → alice, bob
    assert solution(queries) == [
        "true", "true", "300", "400",
        "bob(400/500), alice(300/1000)",
        "true",
        "alice(300/1000), bob(0/500)",
    ]


def test_worked_example_from_spec():
    queries = [
        ["CREATE_USER",  "1",  "alice", "1000"],
        ["CREATE_USER",  "2",  "bob",   "400"],
        ["CREATE_USER",  "3",  "carol", "200"],
        ["UPLOAD",       "4",  "alice", "doc",   "800"],
        ["UPLOAD",       "5",  "bob",   "img",   "300"],
        ["GET_USAGE",    "6",  "alice"],
        ["GET_USAGE",    "7",  "dave"],
        ["TOP_K_USERS",  "8",  "2"],
        ["TOP_K_USERS",  "9",  "5"],
        ["DELETE",       "10", "bob",   "img"],
        ["TOP_K_USERS",  "11", "3"],
    ]
    assert solution(queries) == [
        "true", "true", "true", "800", "300",
        "800/1000",
        "",
        "alice(800/1000), bob(300/400)",
        "alice(800/1000), bob(300/400), carol(0/200)",
        "true",
        "alice(800/1000), bob(0/400), carol(0/200)",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 2 complete — move to Level 3.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
