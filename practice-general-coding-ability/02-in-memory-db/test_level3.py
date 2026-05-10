"""
Level 3 tests — run with: python test_level3.py

Tests TTL / expiration on top of all Level 1 and Level 2 operations.
No external deps. Uses only the standard library.
"""

import sys
import traceback
from solution import solution


# ----- Level 1+2 regression -----


def test_l1_set_get_unaffected():
    queries = [
        ["SET", "1", "k", "f", "v"],
        ["GET", "2", "k", "f"],
    ]
    assert solution(queries) == ["", "v"]


def test_l2_scan_unaffected():
    queries = [
        ["SET",  "1", "row", "b", "2"],
        ["SET",  "2", "row", "a", "1"],
        ["SCAN", "3", "row"],
    ]
    assert solution(queries) == ["", "", "a(1), b(2)"]


# ----- SET_WITH_TTL basics -----


def test_set_with_ttl_returns_empty():
    queries = [["SET_WITH_TTL", "10", "k", "f", "val", "5"]]
    assert solution(queries) == [""]


def test_get_before_expiry():
    # Set at ts=10, ttl=5 → expiry=15. GET at ts=14 → valid.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "hello", "5"],
        ["GET",          "14", "k", "f"],
    ]
    assert solution(queries) == ["", "hello"]


def test_get_at_exact_expiry_returns_empty():
    # Expiry = 10 + 5 = 15. GET at ts=15 → EXPIRED (half-open: [10, 15)).
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "hello", "5"],
        ["GET",          "15", "k", "f"],
    ]
    assert solution(queries) == ["", ""]


def test_get_after_expiry_returns_empty():
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "hello", "5"],
        ["GET",          "20", "k", "f"],
    ]
    assert solution(queries) == ["", ""]


def test_get_one_before_expiry_is_valid():
    # Expiry = 10+5=15. GET at ts=14 → valid.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "hello", "5"],
        ["GET",          "14", "k", "f"],
    ]
    assert solution(queries) == ["", "hello"]


# ----- Plain SET clears TTL -----


def test_set_overwrites_ttl_entry_clears_expiry():
    # Entry expires at 15. Overwrite with plain SET at ts=12. Now it never expires.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "temp",      "5"],
        ["SET",          "12", "k", "f", "permanent"],
        ["GET",          "20", "k", "f"],   # long after original expiry=15
        ["GET",          "50", "k", "f"],   # even further out
    ]
    assert solution(queries) == ["", "", "permanent", "permanent"]


# ----- DELETE respects TTL -----


def test_delete_expired_returns_false():
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val", "5"],
        ["DELETE",       "15", "k", "f"],   # ts=15 = expiry → expired
    ]
    assert solution(queries) == ["", "false"]


def test_delete_before_expiry_returns_true():
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val", "5"],
        ["DELETE",       "14", "k", "f"],
    ]
    assert solution(queries) == ["", "true"]


# ----- UPDATE_TTL -----


def test_update_ttl_returns_true_and_extends_life():
    # Expiry was 15. UPDATE_TTL at ts=12 with ttl=20 → new expiry=32.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val",  "5"],
        ["UPDATE_TTL",   "12", "k", "f",          "20"],
        ["GET",          "15", "k", "f"],   # would have expired without UPDATE_TTL
        ["GET",          "31", "k", "f"],   # still valid (32-1)
        ["GET",          "32", "k", "f"],   # expired (ts=32 >= expiry=32)
    ]
    assert solution(queries) == ["", "true", "val", "val", ""]


def test_update_ttl_on_expired_returns_false():
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val", "5"],
        ["UPDATE_TTL",   "15", "k", "f",          "10"],  # ts=15 = expiry → expired
    ]
    assert solution(queries) == ["", "false"]


def test_update_ttl_on_missing_key_returns_false():
    queries = [["UPDATE_TTL", "10", "ghost", "f", "5"]]
    assert solution(queries) == ["false"]


def test_update_ttl_on_plain_set_entry():
    # Plain SET entries have no TTL. UPDATE_TTL should work and add an expiry.
    queries = [
        ["SET",        "1",  "k", "f", "val"],
        ["UPDATE_TTL", "10", "k", "f", "5"],    # new expiry = 10+5 = 15
        ["GET",        "14", "k", "f"],          # valid
        ["GET",        "15", "k", "f"],          # expired
    ]
    assert solution(queries) == ["", "true", "val", ""]


# ----- SCAN respects TTL -----


def test_scan_excludes_expired_fields():
    # a expires at 15, b never expires
    queries = [
        ["SET_WITH_TTL", "10", "row", "a", "1", "5"],
        ["SET",          "11", "row", "b", "2"],
        ["SCAN",         "15", "row"],   # ts=15 → a expired, only b
    ]
    assert solution(queries) == ["", "", "b(2)"]


def test_scan_by_prefix_excludes_expired():
    # tx_a expires at 20, tx_b never expires
    queries = [
        ["SET_WITH_TTL", "10", "row", "tx_a", "1", "10"],  # expiry=20
        ["SET",          "11", "row", "tx_b", "2"],
        ["SCAN_BY_PREFIX", "20", "row", "tx_"],   # ts=20 → tx_a expired
    ]
    assert solution(queries) == ["", "", "tx_b(2)"]


def test_scan_returns_empty_when_all_expired():
    queries = [
        ["SET_WITH_TTL", "10", "row", "a", "1", "5"],
        ["SET_WITH_TTL", "11", "row", "b", "2", "4"],  # expiry=15
        ["SCAN",         "15", "row"],   # both expired at ts=15
    ]
    assert solution(queries) == ["", "", ""]


# ----- SET_WITH_TTL overwriting -----


def test_set_with_ttl_overwrites_ttl_entry():
    # First TTL expires at 15. Overwrite at ts=12 with new TTL → expiry=22.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "old", "5"],
        ["SET_WITH_TTL", "12", "k", "f", "new", "10"],  # expiry=22
        ["GET",          "15", "k", "f"],   # old expiry passed, new still valid
        ["GET",          "21", "k", "f"],   # valid
        ["GET",          "22", "k", "f"],   # expired
    ]
    assert solution(queries) == ["", "", "new", "new", ""]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 3 complete — move on to Level 4.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
