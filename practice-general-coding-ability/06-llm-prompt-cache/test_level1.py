"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_cache_put_returns_empty():
    queries = [["CACHE_PUT", "1", "hello", "world"]]
    assert solution(queries) == [""]


def test_cache_get_hit():
    queries = [
        ["CACHE_PUT", "1", "hello", "world"],
        ["CACHE_GET", "2", "hello"],
    ]
    assert solution(queries) == ["", "world"]


def test_cache_get_miss():
    queries = [["CACHE_GET", "1", "nonexistent"]]
    assert solution(queries) == [""]


def test_cache_put_overwrite():
    queries = [
        ["CACHE_PUT", "1", "key", "old-value"],
        ["CACHE_PUT", "2", "key", "new-value"],
        ["CACHE_GET", "3", "key"],
    ]
    assert solution(queries) == ["", "", "new-value"]


def test_cache_delete_existing():
    queries = [
        ["CACHE_PUT",    "1", "key", "val"],
        ["CACHE_DELETE", "2", "key"],
    ]
    assert solution(queries) == ["", "true"]


def test_cache_delete_nonexistent():
    queries = [["CACHE_DELETE", "1", "ghost"]]
    assert solution(queries) == ["false"]


def test_cache_delete_then_get_miss():
    queries = [
        ["CACHE_PUT",    "1", "key", "val"],
        ["CACHE_DELETE", "2", "key"],
        ["CACHE_GET",    "3", "key"],
    ]
    assert solution(queries) == ["", "true", ""]


def test_cache_delete_twice():
    queries = [
        ["CACHE_PUT",    "1", "key", "val"],
        ["CACHE_DELETE", "2", "key"],
        ["CACHE_DELETE", "3", "key"],
    ]
    assert solution(queries) == ["", "true", "false"]


def test_multiple_keys_independent():
    queries = [
        ["CACHE_PUT", "1", "A", "resp-A"],
        ["CACHE_PUT", "2", "B", "resp-B"],
        ["CACHE_GET", "3", "A"],
        ["CACHE_GET", "4", "B"],
        ["CACHE_DELETE", "5", "A"],
        ["CACHE_GET", "6", "A"],
        ["CACHE_GET", "7", "B"],
    ]
    assert solution(queries) == ["", "", "resp-A", "resp-B", "true", "", "resp-B"]


def test_overwrite_then_delete():
    queries = [
        ["CACHE_PUT",    "1", "p", "v1"],
        ["CACHE_PUT",    "2", "p", "v2"],
        ["CACHE_DELETE", "3", "p"],
        ["CACHE_GET",    "4", "p"],
    ]
    assert solution(queries) == ["", "", "true", ""]


def test_prompt_with_spaces():
    queries = [
        ["CACHE_PUT", "1", "What is the capital of France?", "Paris"],
        ["CACHE_GET", "2", "What is the capital of France?"],
        ["CACHE_GET", "3", "What is the capital of Spain?"],
    ]
    assert solution(queries) == ["", "Paris", ""]


def test_worked_example_from_spec():
    queries = [
        ["CACHE_PUT",    "1", "What is 2+2?", "4"],
        ["CACHE_GET",    "2", "What is 2+2?"],
        ["CACHE_GET",    "3", "What is 3+3?"],
        ["CACHE_PUT",    "4", "What is 2+2?", "Four"],
        ["CACHE_GET",    "5", "What is 2+2?"],
        ["CACHE_DELETE", "6", "What is 2+2?"],
        ["CACHE_DELETE", "7", "What is 2+2?"],
        ["CACHE_GET",    "8", "What is 2+2?"],
    ]
    assert solution(queries) == ["", "4", "", "", "Four", "true", "false", ""]


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
