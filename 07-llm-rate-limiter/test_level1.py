"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_register_new_key_returns_true():
    queries = [["REGISTER_KEY", "1", "key-A", "1000"]]
    assert solution(queries) == ["true"]


def test_register_duplicate_returns_false():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "1000"],
        ["REGISTER_KEY", "2", "key-A", "500"],
    ]
    assert solution(queries) == ["true", "false"]


def test_register_multiple_distinct_keys():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "1000"],
        ["REGISTER_KEY", "2", "key-B", "2000"],
        ["REGISTER_KEY", "3", "key-C", "500"],
    ]
    assert solution(queries) == ["true", "true", "true"]


def test_bucket_starts_full():
    queries = [
        ["REGISTER_KEY",  "1", "key-A", "1000"],
        ["GET_REMAINING", "2", "key-A"],
    ]
    assert solution(queries) == ["true", "1000"]


def test_consume_returns_remaining():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "1000"],
        ["CONSUME",      "2", "key-A", "300"],
    ]
    assert solution(queries) == ["true", "700"]


def test_consume_multiple_deductions():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "1000"],
        ["CONSUME",      "2", "key-A", "300"],
        ["CONSUME",      "3", "key-A", "200"],
        ["GET_REMAINING","4", "key-A"],
    ]
    assert solution(queries) == ["true", "700", "500", "500"]


def test_consume_insufficient_denied_no_deduction():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "500"],
        ["CONSUME",      "2", "key-A", "300"],
        ["CONSUME",      "3", "key-A", "300"],  # only 200 left — denied
        ["GET_REMAINING","4", "key-A"],          # still 200
    ]
    assert solution(queries) == ["true", "200", "", "200"]


def test_consume_exact_amount_leaves_zero():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "500"],
        ["CONSUME",      "2", "key-A", "500"],
        ["GET_REMAINING","3", "key-A"],
    ]
    assert solution(queries) == ["true", "0", "0"]


def test_consume_on_missing_key_returns_empty():
    queries = [["CONSUME", "1", "ghost", "100"]]
    assert solution(queries) == [""]


def test_get_remaining_on_missing_key_returns_empty():
    queries = [["GET_REMAINING", "1", "ghost"]]
    assert solution(queries) == [""]


def test_keys_are_isolated():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "1000"],
        ["REGISTER_KEY", "2", "key-B", "500"],
        ["CONSUME",      "3", "key-A", "800"],
        ["GET_REMAINING","4", "key-B"],   # key-B untouched
        ["CONSUME",      "5", "key-B", "600"],  # denied — only 500
        ["GET_REMAINING","6", "key-B"],   # still 500
    ]
    assert solution(queries) == ["true", "true", "200", "500", "", "500"]


def test_duplicate_register_does_not_reset_bucket():
    queries = [
        ["REGISTER_KEY", "1", "key-A", "1000"],
        ["CONSUME",      "2", "key-A", "400"],
        ["REGISTER_KEY", "3", "key-A", "9999"],   # dup — must not reset bucket
        ["GET_REMAINING","4", "key-A"],             # still 600
    ]
    assert solution(queries) == ["true", "600", "false", "600"]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_KEY",  "1", "key-A", "1000"],
        ["REGISTER_KEY",  "2", "key-A", "500"],
        ["CONSUME",       "3", "key-A", "300"],
        ["CONSUME",       "4", "key-B", "100"],
        ["GET_REMAINING", "5", "key-A"],
        ["CONSUME",       "6", "key-A", "800"],
        ["GET_REMAINING", "7", "key-A"],
    ]
    assert solution(queries) == ["true", "false", "700", "", "700", "", "700"]


def test_large_token_counts_no_overflow():
    queries = [
        ["REGISTER_KEY", "1", "whale", "10000000000000"],
        ["CONSUME",      "2", "whale", "9999999999999"],
        ["GET_REMAINING","3", "whale"],
    ]
    assert solution(queries) == ["true", "1", "1"]


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
