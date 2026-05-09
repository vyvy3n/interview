"""
Level 2 tests — run with: python test_level2.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_hit_count_zero_after_put():
    queries = [
        ["CACHE_PUT",  "1", "prompt", "response"],
        ["HIT_COUNT",  "2", "prompt"],
    ]
    assert solution(queries) == ["", "0"]


def test_hit_count_increments_on_get_hit():
    queries = [
        ["CACHE_PUT",  "1", "p", "r"],
        ["CACHE_GET",  "2", "p"],
        ["CACHE_GET",  "3", "p"],
        ["HIT_COUNT",  "4", "p"],
    ]
    assert solution(queries) == ["", "r", "r", "2"]


def test_hit_count_miss_does_not_count():
    queries = [
        ["CACHE_PUT",  "1", "p", "r"],
        ["CACHE_GET",  "2", "missing"],
        ["HIT_COUNT",  "3", "p"],
    ]
    assert solution(queries) == ["", "", "0"]


def test_hit_count_missing_prompt_returns_empty():
    queries = [
        ["HIT_COUNT", "1", "nonexistent"],
    ]
    assert solution(queries) == [""]


def test_hit_count_deleted_returns_empty():
    queries = [
        ["CACHE_PUT",    "1", "p", "r"],
        ["CACHE_GET",    "2", "p"],
        ["CACHE_DELETE", "3", "p"],
        ["HIT_COUNT",    "4", "p"],
    ]
    assert solution(queries) == ["", "r", "true", ""]


def test_hit_count_resets_after_delete_and_reput():
    queries = [
        ["CACHE_PUT",    "1", "p", "r"],
        ["CACHE_GET",    "2", "p"],
        ["CACHE_GET",    "3", "p"],
        ["CACHE_DELETE", "4", "p"],
        ["CACHE_PUT",    "5", "p", "r2"],
        ["HIT_COUNT",    "6", "p"],
    ]
    assert solution(queries) == ["", "r", "r", "true", "", "0"]


def test_top_k_hot_empty_cache():
    queries = [["TOP_K_HOT", "1", "3"]]
    assert solution(queries) == [""]


def test_top_k_hot_basic_sorting():
    queries = [
        ["CACHE_PUT", "1", "A", "r"],
        ["CACHE_PUT", "2", "B", "r"],
        ["CACHE_PUT", "3", "C", "r"],
        ["CACHE_GET", "4", "A"],
        ["CACHE_GET", "5", "A"],
        ["CACHE_GET", "6", "B"],
        ["TOP_K_HOT", "7", "3"],
    ]
    assert solution(queries) == ["", "", "", "r", "r", "r", "A(2), B(1), C(0)"]


def test_top_k_hot_fewer_than_k():
    queries = [
        ["CACHE_PUT", "1", "X", "r"],
        ["TOP_K_HOT", "2", "10"],
    ]
    assert solution(queries) == ["", "X(0)"]


def test_top_k_hot_tiebreak_alphabetical():
    queries = [
        ["CACHE_PUT", "1", "zebra", "r"],
        ["CACHE_PUT", "2", "apple", "r"],
        ["CACHE_PUT", "3", "mango", "r"],
        ["TOP_K_HOT", "4", "3"],
    ]
    # All have 0 hits — sorted alphabetically ASC
    assert solution(queries) == ["", "", "", "apple(0), mango(0), zebra(0)"]


def test_top_k_hot_excludes_deleted():
    queries = [
        ["CACHE_PUT",    "1", "A", "r"],
        ["CACHE_PUT",    "2", "B", "r"],
        ["CACHE_GET",    "3", "A"],
        ["CACHE_DELETE", "4", "A"],
        ["TOP_K_HOT",    "5", "5"],
    ]
    assert solution(queries) == ["", "", "r", "true", "B(0)"]


def test_top_k_hot_limits_to_k():
    queries = [
        ["CACHE_PUT", "1", "A", "r"],
        ["CACHE_PUT", "2", "B", "r"],
        ["CACHE_PUT", "3", "C", "r"],
        ["CACHE_GET", "4", "A"],
        ["TOP_K_HOT", "5", "2"],
    ]
    assert solution(queries) == ["", "", "", "r", "A(1), B(0)"]


def test_worked_example_from_spec():
    queries = [
        ["CACHE_PUT",    "1",  "A", "response-A"],
        ["CACHE_PUT",    "2",  "B", "response-B"],
        ["CACHE_PUT",    "3",  "C", "response-C"],
        ["CACHE_GET",    "4",  "A"],
        ["CACHE_GET",    "5",  "A"],
        ["CACHE_GET",    "6",  "B"],
        ["CACHE_GET",    "7",  "Z"],
        ["HIT_COUNT",    "8",  "A"],
        ["HIT_COUNT",    "9",  "B"],
        ["HIT_COUNT",    "10", "C"],
        ["HIT_COUNT",    "11", "Z"],
        ["TOP_K_HOT",    "12", "2"],
        ["CACHE_DELETE", "13", "A"],
        ["TOP_K_HOT",    "14", "5"],
        ["CACHE_PUT",    "15", "A", "new-response-A"],
        ["HIT_COUNT",    "16", "A"],
        ["TOP_K_HOT",    "17", "3"],
    ]
    assert solution(queries) == [
        "", "", "", "response-A", "response-A", "response-B", "",
        "2", "1", "0", "",
        "A(2), B(1)",
        "true",
        "B(1), C(0)",
        "",
        "0",
        "B(1), A(0), C(0)",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 2 complete — commit and request Level 3.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
