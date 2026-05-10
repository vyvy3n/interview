"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_set_returns_empty_string():
    queries = [["SET", "1", "user", "name", "alice"]]
    assert solution(queries) == [""]


def test_get_existing_field():
    queries = [
        ["SET", "1", "user", "name", "alice"],
        ["GET", "2", "user", "name"],
    ]
    assert solution(queries) == ["", "alice"]


def test_get_missing_key_returns_empty():
    queries = [["GET", "1", "ghost", "name"]]
    assert solution(queries) == [""]


def test_get_missing_field_returns_empty():
    queries = [
        ["SET", "1", "user", "name", "alice"],
        ["GET", "2", "user", "email"],
    ]
    assert solution(queries) == ["", ""]


def test_set_overwrites_existing_value():
    queries = [
        ["SET", "1", "user", "name", "alice"],
        ["SET", "2", "user", "name", "ALICE"],
        ["GET", "3", "user", "name"],
    ]
    assert solution(queries) == ["", "", "ALICE"]


def test_delete_existing_field_returns_true():
    queries = [
        ["SET",    "1", "user", "name", "alice"],
        ["DELETE", "2", "user", "name"],
    ]
    assert solution(queries) == ["", "true"]


def test_delete_missing_key_returns_false():
    queries = [["DELETE", "1", "ghost", "name"]]
    assert solution(queries) == ["false"]


def test_delete_missing_field_returns_false():
    queries = [
        ["SET",    "1", "user", "name", "alice"],
        ["DELETE", "2", "user", "email"],
    ]
    assert solution(queries) == ["", "false"]


def test_delete_same_field_twice():
    queries = [
        ["SET",    "1", "user", "name", "alice"],
        ["DELETE", "2", "user", "name"],
        ["DELETE", "3", "user", "name"],
    ]
    assert solution(queries) == ["", "true", "false"]


def test_get_after_delete_returns_empty():
    queries = [
        ["SET",    "1", "user", "name", "alice"],
        ["DELETE", "2", "user", "name"],
        ["GET",    "3", "user", "name"],
    ]
    assert solution(queries) == ["", "true", ""]


def test_multiple_keys_are_independent():
    queries = [
        ["SET", "1", "user:1", "name", "alice"],
        ["SET", "2", "user:2", "name", "bob"],
        ["GET", "3", "user:1", "name"],
        ["GET", "4", "user:2", "name"],
        ["GET", "5", "user:1", "email"],
    ]
    assert solution(queries) == ["", "", "alice", "bob", ""]


def test_multiple_fields_same_key():
    queries = [
        ["SET", "1", "record", "a", "1"],
        ["SET", "2", "record", "b", "2"],
        ["SET", "3", "record", "c", "3"],
        ["GET", "4", "record", "a"],
        ["GET", "5", "record", "b"],
        ["GET", "6", "record", "c"],
    ]
    assert solution(queries) == ["", "", "", "1", "2", "3"]


def test_combined_realistic_sequence():
    queries = [
        ["SET",    "1",  "product:1", "name",  "Widget"],
        ["SET",    "2",  "product:1", "price", "9.99"],
        ["SET",    "3",  "product:2", "name",  "Gadget"],
        ["GET",    "4",  "product:1", "name"],
        ["GET",    "5",  "product:2", "price"],
        ["DELETE", "6",  "product:1", "price"],
        ["GET",    "7",  "product:1", "price"],
        ["SET",    "8",  "product:1", "price", "12.99"],
        ["GET",    "9",  "product:1", "price"],
        ["DELETE", "10", "product:3", "name"],
    ]
    assert solution(queries) == ["", "", "", "Widget", "", "true", "", "", "12.99", "false"]


def test_value_with_special_characters():
    # Values can contain any non-space string characters
    queries = [
        ["SET", "1", "meta", "url", "https://example.com/path?q=1"],
        ["GET", "2", "meta", "url"],
    ]
    assert solution(queries) == ["", "https://example.com/path?q=1"]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 1 complete — move on to Level 2.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
