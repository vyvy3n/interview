"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_create_user_new():
    queries = [["CREATE_USER", "1", "alice", "1000"]]
    assert solution(queries) == ["true"]


def test_create_user_duplicate_returns_false():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "alice", "500"],
    ]
    assert solution(queries) == ["true", "false"]


def test_create_multiple_distinct_users():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["CREATE_USER", "3", "carol", "200"],
    ]
    assert solution(queries) == ["true", "true", "true"]


def test_upload_to_nonexistent_user_returns_empty():
    queries = [["UPLOAD", "1", "ghost", "doc", "100"]]
    assert solution(queries) == [""]


def test_upload_returns_total_used():
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["UPLOAD",      "2", "alice", "doc",   "300"],
        ["UPLOAD",      "3", "alice", "photo", "200"],
    ]
    assert solution(queries) == ["true", "300", "500"]


def test_upload_at_exact_quota_allowed():
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["UPLOAD",      "2", "alice", "doc", "500"],
    ]
    assert solution(queries) == ["true", "500"]


def test_upload_exceeding_quota_returns_empty_no_state_change():
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["UPLOAD",      "2", "alice", "doc",   "300"],
        ["UPLOAD",      "3", "alice", "photo", "300"],  # 300+300=600 > 500 — reject
        ["UPLOAD",      "4", "alice", "video", "200"],  # 300+200=500 — allowed
    ]
    assert solution(queries) == ["true", "300", "", "500"]


def test_upload_overwrite_same_file_larger():
    # overwrite: diff = 400 - 200 = +200; new total = 200 + 200 = 400
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["UPLOAD",      "2", "alice", "doc", "200"],
        ["UPLOAD",      "3", "alice", "doc", "400"],
    ]
    assert solution(queries) == ["true", "200", "400"]


def test_upload_overwrite_same_file_smaller():
    # overwrite: diff = 100 - 300 = -200; new total = 300 - 200 = 100
    queries = [
        ["CREATE_USER", "1", "alice", "1000"],
        ["UPLOAD",      "2", "alice", "doc", "300"],
        ["UPLOAD",      "3", "alice", "doc", "100"],
    ]
    assert solution(queries) == ["true", "300", "100"]


def test_upload_overwrite_exceeding_quota_rejected():
    # alice used=400, quota=500; overwrite doc(300) with doc(200) is fine (net -100) → used=100
    # then try overwrite photo(100) with photo(500): 100 + 400 = 500, exactly quota → allowed
    # then try overwrite photo(500) with photo(600): 500 + 100 = 600 > 500 → reject
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["UPLOAD",      "2", "alice", "doc",   "300"],
        ["UPLOAD",      "3", "alice", "photo", "100"],
        ["UPLOAD",      "4", "alice", "doc",   "200"],   # 100 + 200 = 300 net; total = 300 → "300"? no:
        # after step 3: used = 300+100=400. step 4: overwrite doc(300) with doc(200): diff=-100; used=300. → "300"
        ["UPLOAD",      "5", "alice", "photo", "300"],   # overwrite photo(100) with photo(300): diff=+200; used=300+200=500 → "500"
        ["UPLOAD",      "6", "alice", "photo", "600"],   # overwrite photo(300) with photo(600): diff=+300; 500+300=800 > 500 → ""
    ]
    assert solution(queries) == ["true", "300", "400", "300", "500", ""]


def test_separate_file_namespaces():
    # alice and bob each have a file called "doc" — completely independent
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["CREATE_USER", "2", "bob",   "500"],
        ["UPLOAD",      "3", "alice", "doc", "200"],
        ["UPLOAD",      "4", "bob",   "doc", "300"],
        ["DELETE",      "5", "alice", "doc"],
    ]
    assert solution(queries) == ["true", "true", "200", "300", "true"]


def test_delete_file_frees_space():
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["UPLOAD",      "2", "alice", "doc",   "300"],
        ["UPLOAD",      "3", "alice", "photo", "300"],  # exceeds → ""
        ["DELETE",      "4", "alice", "doc"],
        ["UPLOAD",      "5", "alice", "photo", "300"],  # now fits: 0+300=300
    ]
    assert solution(queries) == ["true", "300", "", "true", "300"]


def test_delete_nonexistent_file_returns_false():
    queries = [
        ["CREATE_USER", "1", "alice", "500"],
        ["DELETE",      "2", "alice", "missing"],
    ]
    assert solution(queries) == ["true", "false"]


def test_delete_nonexistent_user_returns_false():
    queries = [["DELETE", "1", "ghost", "doc"]]
    assert solution(queries) == ["false"]


def test_worked_example_from_spec():
    queries = [
        ["CREATE_USER", "1",  "alice", "1000"],
        ["CREATE_USER", "2",  "alice", "500"],
        ["CREATE_USER", "3",  "bob",   "400"],
        ["UPLOAD",      "4",  "alice", "report", "300"],
        ["UPLOAD",      "5",  "alice", "photo",  "500"],
        ["UPLOAD",      "6",  "alice", "video",  "400"],
        ["UPLOAD",      "7",  "alice", "report", "100"],
        ["UPLOAD",      "8",  "bob",   "report", "300"],
        ["DELETE",      "9",  "alice", "photo"],
        ["DELETE",      "10", "bob",   "missing"],
        ["UPLOAD",      "11", "alice", "video",  "400"],
    ]
    assert solution(queries) == [
        "true", "false", "true", "300", "800", "", "600", "300", "true", "false", "500",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 1 complete — move to Level 2.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
