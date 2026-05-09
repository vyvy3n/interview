"""
Level 2 tests — run with: python test_level2.py

Tests SCAN and SCAN_BY_PREFIX on top of all Level 1 operations.
No external deps. Uses only the standard library.
"""

import sys
import traceback
from solution import solution


# ----- Level 1 regression -----


def test_l1_set_get_still_works():
    queries = [
        ["SET", "1", "k", "f", "v"],
        ["GET", "2", "k", "f"],
    ]
    assert solution(queries) == ["", "v"]


def test_l1_delete_still_works():
    queries = [
        ["SET",    "1", "k", "f", "v"],
        ["DELETE", "2", "k", "f"],
        ["GET",    "3", "k", "f"],
    ]
    assert solution(queries) == ["", "true", ""]


# ----- SCAN -----


def test_scan_single_field():
    queries = [
        ["SET",  "1", "row", "alpha", "1"],
        ["SCAN", "2", "row"],
    ]
    assert solution(queries) == ["", "alpha(1)"]


def test_scan_multiple_fields_sorted():
    # Fields: zebra, apple, mango — must come back sorted alpha
    queries = [
        ["SET",  "1", "row", "zebra", "z"],
        ["SET",  "2", "row", "apple", "a"],
        ["SET",  "3", "row", "mango", "m"],
        ["SCAN", "4", "row"],
    ]
    assert solution(queries) == ["", "", "", "apple(a), mango(m), zebra(z)"]


def test_scan_missing_key_returns_empty():
    queries = [["SCAN", "1", "ghost"]]
    assert solution(queries) == [""]


def test_scan_after_all_fields_deleted():
    queries = [
        ["SET",    "1", "row", "x", "1"],
        ["DELETE", "2", "row", "x"],
        ["SCAN",   "3", "row"],
    ]
    assert solution(queries) == ["", "true", ""]


def test_scan_reflects_overwritten_value():
    queries = [
        ["SET",  "1", "row", "field", "old"],
        ["SET",  "2", "row", "field", "new"],
        ["SCAN", "3", "row"],
    ]
    assert solution(queries) == ["", "", "field(new)"]


def test_scan_multiple_keys_independent():
    queries = [
        ["SET",  "1", "a", "x", "1"],
        ["SET",  "2", "b", "y", "2"],
        ["SCAN", "3", "a"],
        ["SCAN", "4", "b"],
    ]
    assert solution(queries) == ["", "", "x(1)", "y(2)"]


# ----- SCAN_BY_PREFIX -----


def test_scan_by_prefix_basic():
    queries = [
        ["SET",            "1", "row", "abc",  "1"],
        ["SET",            "2", "row", "abd",  "2"],
        ["SET",            "3", "row", "xyz",  "3"],
        ["SCAN_BY_PREFIX", "4", "row", "ab"],
    ]
    assert solution(queries) == ["", "", "", "abc(1), abd(2)"]


def test_scan_by_prefix_no_match_returns_empty():
    queries = [
        ["SET",            "1", "row", "abc", "1"],
        ["SCAN_BY_PREFIX", "2", "row", "z"],
    ]
    assert solution(queries) == ["", ""]


def test_scan_by_prefix_missing_key_returns_empty():
    queries = [["SCAN_BY_PREFIX", "1", "ghost", "any"]]
    assert solution(queries) == [""]


def test_scan_by_prefix_exact_field_name():
    # prefix equals the full field name — should match that one field
    queries = [
        ["SET",            "1", "row", "exact", "hit"],
        ["SET",            "2", "row", "exactness", "miss"],
        ["SCAN_BY_PREFIX", "3", "row", "exact"],
    ]
    # "exact" starts with "exact" → yes; "exactness" starts with "exact" → yes too
    assert solution(queries) == ["", "", "exact(hit), exactness(miss)"]


def test_scan_by_prefix_case_sensitive():
    queries = [
        ["SET",            "1", "row", "Name", "alice"],
        ["SET",            "2", "row", "name", "bob"],
        ["SCAN_BY_PREFIX", "3", "row", "N"],
        ["SCAN_BY_PREFIX", "4", "row", "n"],
    ]
    assert solution(queries) == ["", "", "Name(alice)", "name(bob)"]


def test_scan_by_prefix_sorted_result():
    queries = [
        ["SET",            "1", "row", "tx_c", "3"],
        ["SET",            "2", "row", "tx_a", "1"],
        ["SET",            "3", "row", "tx_b", "2"],
        ["SET",            "4", "row", "other", "x"],
        ["SCAN_BY_PREFIX", "5", "row", "tx_"],
    ]
    assert solution(queries) == ["", "", "", "", "tx_a(1), tx_b(2), tx_c(3)"]


def test_combined_scan_and_delete():
    # Build a row, delete one field, SCAN and SCAN_BY_PREFIX
    queries = [
        ["SET",            "1", "cfg", "db_host",     "localhost"],
        ["SET",            "2", "cfg", "db_port",     "5432"],
        ["SET",            "3", "cfg", "cache_host",  "redis"],
        ["SET",            "4", "cfg", "cache_port",  "6379"],
        ["SCAN",           "5", "cfg"],
        ["DELETE",         "6", "cfg", "db_port"],
        ["SCAN_BY_PREFIX", "7", "cfg", "db_"],
        ["SCAN_BY_PREFIX", "8", "cfg", "cache_"],
    ]
    assert solution(queries) == [
        "",
        "",
        "",
        "",
        "cache_host(redis), cache_port(6379), db_host(localhost), db_port(5432)",
        "true",
        "db_host(localhost)",
        "cache_host(redis), cache_port(6379)",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 2 complete — move on to Level 3.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
