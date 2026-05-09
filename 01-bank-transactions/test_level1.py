"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_create_single():
    queries = [["CREATE_ACCOUNT", "1", "alice"]]
    assert solution(queries) == ["true"]


def test_create_duplicate_returns_false():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "alice"],
    ]
    assert solution(queries) == ["true", "false"]


def test_create_multiple_distinct_accounts():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["CREATE_ACCOUNT", "3", "carol"],
    ]
    assert solution(queries) == ["true", "true", "true"]


def test_deposit_to_nonexistent_returns_empty():
    queries = [["DEPOSIT", "1", "ghost", "100"]]
    assert solution(queries) == [""]


def test_deposit_returns_new_balance():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT", "2", "alice", "100"],
        ["DEPOSIT", "3", "alice", "50"],
    ]
    assert solution(queries) == ["true", "100", "150"]


def test_pay_with_sufficient_funds():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT", "2", "alice", "100"],
        ["PAY", "3", "alice", "30"],
    ]
    assert solution(queries) == ["true", "100", "70"]


def test_pay_insufficient_funds_returns_empty_and_no_charge():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT", "2", "alice", "100"],
        ["PAY", "3", "alice", "200"],   # insufficient — must not deduct
        ["PAY", "4", "alice", "100"],   # should still work, balance unchanged
    ]
    assert solution(queries) == ["true", "100", "", "0"]


def test_pay_to_nonexistent_returns_empty():
    queries = [["PAY", "1", "ghost", "10"]]
    assert solution(queries) == [""]


def test_pay_exact_balance_to_zero():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT", "2", "alice", "50"],
        ["PAY", "3", "alice", "50"],
    ]
    assert solution(queries) == ["true", "50", "0"]


def test_accounts_are_isolated():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT", "3", "alice", "100"],
        ["PAY", "4", "bob", "10"],          # bob has 0
        ["DEPOSIT", "5", "bob", "200"],
        ["PAY", "6", "alice", "100"],       # alice down to 0
        ["PAY", "7", "alice", "1"],         # alice empty
    ]
    assert solution(queries) == ["true", "true", "100", "", "200", "0", ""]


def test_combined_realistic_sequence():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT", "3", "alice", "1000"],
        ["DEPOSIT", "4", "bob", "500"],
        ["PAY", "5", "alice", "300"],
        ["PAY", "6", "bob", "600"],         # insufficient
        ["DEPOSIT", "7", "bob", "200"],
        ["PAY", "8", "bob", "700"],
        ["CREATE_ACCOUNT", "9", "alice"],   # duplicate
    ]
    assert solution(queries) == [
        "true", "true", "1000", "500", "700", "", "700", "0", "false",
    ]


def test_large_balance_no_overflow():
    queries = [
        ["CREATE_ACCOUNT", "1", "whale"],
        ["DEPOSIT", "2", "whale", "1000000000000"],
        ["DEPOSIT", "3", "whale", "1000000000000"],
        ["PAY", "4", "whale", "500000000000"],
    ]
    assert solution(queries) == ["true", "1000000000000", "2000000000000", "1500000000000"]


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
