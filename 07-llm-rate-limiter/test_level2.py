"""
Level 2 tests — run with: python test_level2.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_total_consumed_zero_at_registration():
    queries = [
        ["REGISTER_KEY",   "1", "key-A", "1000"],
        ["TOTAL_CONSUMED", "2", "key-A"],
    ]
    assert solution(queries) == ["true", "0"]


def test_total_consumed_after_single_consume():
    queries = [
        ["REGISTER_KEY",   "1", "key-A", "1000"],
        ["CONSUME",        "2", "key-A", "400"],
        ["TOTAL_CONSUMED", "3", "key-A"],
    ]
    assert solution(queries) == ["true", "600", "400"]


def test_total_consumed_accumulates():
    queries = [
        ["REGISTER_KEY",   "1", "key-A", "1000"],
        ["CONSUME",        "2", "key-A", "300"],
        ["CONSUME",        "3", "key-A", "200"],
        ["TOTAL_CONSUMED", "4", "key-A"],
    ]
    assert solution(queries) == ["true", "700", "500", "500"]


def test_denied_consume_does_not_count():
    queries = [
        ["REGISTER_KEY",   "1", "key-A", "500"],
        ["CONSUME",        "2", "key-A", "300"],
        ["CONSUME",        "3", "key-A", "300"],   # denied
        ["TOTAL_CONSUMED", "4", "key-A"],           # only 300 counted
    ]
    assert solution(queries) == ["true", "200", "", "300"]


def test_total_consumed_missing_key():
    queries = [["TOTAL_CONSUMED", "1", "ghost"]]
    assert solution(queries) == [""]


def test_top_k_single_key():
    queries = [
        ["REGISTER_KEY",    "1", "key-A", "1000"],
        ["CONSUME",         "2", "key-A", "400"],
        ["TOP_K_CONSUMERS", "3", "5"],
    ]
    assert solution(queries) == ["true", "600", "key-A(400)"]


def test_top_k_all_keys_no_cap():
    queries = [
        ["REGISTER_KEY",    "1", "key-A", "1000"],
        ["REGISTER_KEY",    "2", "key-B", "2000"],
        ["CONSUME",         "3", "key-A", "400"],
        ["CONSUME",         "4", "key-B", "900"],
        ["TOP_K_CONSUMERS", "5", "3"],   # only 2 keys exist
    ]
    assert solution(queries) == ["true", "true", "600", "1100", "key-B(900), key-A(400)"]


def test_top_k_ties_broken_alphabetically():
    queries = [
        ["REGISTER_KEY",    "1", "key-Z", "1000"],
        ["REGISTER_KEY",    "2", "key-A", "1000"],
        ["CONSUME",         "3", "key-Z", "500"],
        ["CONSUME",         "4", "key-A", "500"],
        ["TOP_K_CONSUMERS", "5", "2"],
    ]
    # Both consumed 500 — tie broken alphabetically: key-A before key-Z
    assert solution(queries) == ["true", "true", "500", "500", "key-A(500), key-Z(500)"]


def test_top_k_zero_consumption_included():
    queries = [
        ["REGISTER_KEY",    "1", "key-A", "1000"],
        ["REGISTER_KEY",    "2", "key-B", "500"],
        ["CONSUME",         "3", "key-A", "600"],
        ["TOP_K_CONSUMERS", "4", "2"],
    ]
    # key-B has 0 consumption and is included
    assert solution(queries) == ["true", "true", "400", "key-A(600), key-B(0)"]


def test_top_k_no_keys_returns_empty():
    queries = [["TOP_K_CONSUMERS", "1", "3"]]
    assert solution(queries) == [""]


def test_top_k_with_k_equals_one():
    queries = [
        ["REGISTER_KEY",    "1", "key-A", "1000"],
        ["REGISTER_KEY",    "2", "key-B", "2000"],
        ["CONSUME",         "3", "key-A", "400"],
        ["CONSUME",         "4", "key-B", "900"],
        ["TOP_K_CONSUMERS", "5", "1"],
    ]
    assert solution(queries) == ["true", "true", "600", "1100", "key-B(900)"]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_KEY",    "1",  "key-A", "1000"],
        ["REGISTER_KEY",    "2",  "key-B", "2000"],
        ["CONSUME",         "3",  "key-A", "400"],
        ["CONSUME",         "4",  "key-B", "900"],
        ["CONSUME",         "5",  "key-A", "300"],
        ["CONSUME",         "6",  "key-A", "5000"],
        ["TOTAL_CONSUMED",  "7",  "key-A"],
        ["TOTAL_CONSUMED",  "8",  "ghost"],
        ["TOP_K_CONSUMERS", "9",  "3"],
        ["TOP_K_CONSUMERS", "10", "1"],
    ]
    assert solution(queries) == [
        "true", "true", "600", "1100", "300", "", "700", "",
        "key-B(900), key-A(700)", "key-B(900)",
    ]


def test_top_k_many_keys_sorted_correctly():
    queries = [
        ["REGISTER_KEY",    "1", "key-C", "5000"],
        ["REGISTER_KEY",    "2", "key-A", "5000"],
        ["REGISTER_KEY",    "3", "key-B", "5000"],
        ["CONSUME",         "4", "key-C", "3000"],
        ["CONSUME",         "5", "key-A", "1000"],
        ["CONSUME",         "6", "key-B", "2000"],
        ["TOP_K_CONSUMERS", "7", "3"],
    ]
    assert solution(queries) == [
        "true", "true", "true", "2000", "4000", "3000",
        "key-C(3000), key-B(2000), key-A(1000)",
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
