"""
Level 2 tests — run with: python test_level2.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_transfer_basic():
    # alice sends 100 to bob; alice: 500→400, bob: 200→300; returns new alice balance
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "500"],
        ["DEPOSIT",        "4", "bob",   "200"],
        ["TRANSFER",       "5", "alice", "bob", "100"],
    ]
    assert solution(queries) == ["true", "true", "500", "200", "400"]


def test_transfer_missing_sender():
    # from_id doesn't exist → ""
    queries = [
        ["CREATE_ACCOUNT", "1", "bob"],
        ["DEPOSIT",        "2", "bob", "100"],
        ["TRANSFER",       "3", "ghost", "bob", "50"],
    ]
    assert solution(queries) == ["true", "100", ""]


def test_transfer_missing_receiver():
    # to_id doesn't exist → ""
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT",        "2", "alice", "100"],
        ["TRANSFER",       "3", "alice", "ghost", "50"],
    ]
    assert solution(queries) == ["true", "100", ""]


def test_transfer_self_returns_empty():
    # from_id == to_id → "", even with sufficient funds
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT",        "2", "alice", "500"],
        ["TRANSFER",       "3", "alice", "alice", "100"],
    ]
    assert solution(queries) == ["true", "500", ""]


def test_transfer_insufficient_funds():
    # alice has 50, tries to send 100 → "", balances unchanged
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "50"],
        ["TRANSFER",       "4", "alice", "bob", "100"],
        ["DEPOSIT",        "5", "alice", "0"],   # check alice still has 50
    ]
    # DEPOSIT 0 — wait, amount > 0 per spec. Let's verify balance via TRANSFER that just barely works.
    # Rewrite: after failed transfer, do a successful small deposit
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "50"],
        ["TRANSFER",       "4", "alice", "bob", "100"],   # fails — insufficient
        ["DEPOSIT",        "5", "alice", "10"],            # alice still has 50, now 60
    ]
    assert solution(queries) == ["true", "true", "50", "", "60"]


def test_transfer_exact_balance():
    # Transfer exactly alice's full balance → succeeds, alice at 0
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "200"],
        ["TRANSFER",       "4", "alice", "bob", "200"],
    ]
    assert solution(queries) == ["true", "true", "200", "0"]


def test_transfer_does_not_count_outgoing_on_failure():
    # Failed transfer → alice's outgoing stays 0
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "50"],
        ["TRANSFER",       "4", "alice", "bob", "100"],   # fails
        ["TOP_SPENDERS",   "5", "2"],
    ]
    # alice: 0 outgoing, bob: 0 outgoing; alice before bob alphabetically
    assert solution(queries) == ["true", "true", "50", "", "alice(0), bob(0)"]


def test_top_spenders_pay_only():
    # Only PAY amounts count as outgoing for alice
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "500"],
        ["PAY",            "4", "alice", "150"],
        ["PAY",            "5", "alice", "50"],
        ["TOP_SPENDERS",   "6", "2"],
    ]
    # alice: 200 outgoing, bob: 0
    assert solution(queries) == ["true", "true", "500", "350", "300", "alice(200), bob(0)"]


def test_top_spenders_transfer_counts_outgoing():
    # TRANSFER from alice counts toward alice's outgoing
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "500"],
        ["TRANSFER",       "4", "alice", "bob", "300"],
        ["TOP_SPENDERS",   "5", "2"],
    ]
    # alice: 300 outgoing (from transfer), bob: 0
    assert solution(queries) == ["true", "true", "500", "200", "alice(300), bob(0)"]


def test_top_spenders_combined_pay_and_transfer():
    # alice: PAY 200 + TRANSFER 100 = 300 outgoing; bob: PAY 50 = 50 outgoing
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "1000"],
        ["DEPOSIT",        "4", "bob",   "500"],
        ["PAY",            "5", "alice", "200"],
        ["TRANSFER",       "6", "alice", "bob", "100"],
        ["PAY",            "7", "bob",   "50"],
        ["TOP_SPENDERS",   "8", "2"],
    ]
    # alice: 300 outgoing, bob: 50 outgoing
    assert solution(queries) == ["true", "true", "1000", "500", "800", "700", "550", "alice(300), bob(50)"]


def test_top_spenders_n_larger_than_accounts():
    # n=10 but only 2 accounts — return all
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "100"],
        ["PAY",            "4", "alice", "30"],
        ["TOP_SPENDERS",   "5", "10"],
    ]
    # alice: 30 outgoing, bob: 0; only 2 accounts exist
    assert solution(queries) == ["true", "true", "100", "70", "alice(30), bob(0)"]


def test_top_spenders_tie_broken_alphabetically():
    # carol, alice, bob all have 100 outgoing → alphabetical: alice, bob, carol
    queries = [
        ["CREATE_ACCOUNT", "1",  "carol"],
        ["CREATE_ACCOUNT", "2",  "alice"],
        ["CREATE_ACCOUNT", "3",  "bob"],
        ["DEPOSIT",        "4",  "carol", "500"],
        ["DEPOSIT",        "5",  "alice", "500"],
        ["DEPOSIT",        "6",  "bob",   "500"],
        ["PAY",            "7",  "carol", "100"],
        ["PAY",            "8",  "alice", "100"],
        ["PAY",            "9",  "bob",   "100"],
        ["TOP_SPENDERS",   "10", "3"],
    ]
    assert solution(queries) == [
        "true", "true", "true", "500", "500", "500", "400", "400", "400",
        "alice(100), bob(100), carol(100)",
    ]


def test_top_spenders_n_equals_1():
    # Only the top spender is returned
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "500"],
        ["DEPOSIT",        "4", "bob",   "500"],
        ["PAY",            "5", "bob",   "300"],
        ["PAY",            "6", "alice", "100"],
        ["TOP_SPENDERS",   "7", "1"],
    ]
    # bob: 300 outgoing, alice: 100 outgoing
    assert solution(queries) == ["true", "true", "500", "500", "200", "400", "bob(300)"]


def test_top_spenders_all_zero_outgoing():
    # No one has spent anything — all are tied at 0, sorted alphabetically
    queries = [
        ["CREATE_ACCOUNT", "1", "charlie"],
        ["CREATE_ACCOUNT", "2", "alice"],
        ["CREATE_ACCOUNT", "3", "bob"],
        ["DEPOSIT",        "4", "alice", "100"],
        ["TOP_SPENDERS",   "5", "3"],
    ]
    # alice(0), bob(0), charlie(0) alphabetically
    assert solution(queries) == ["true", "true", "true", "100", "alice(0), bob(0), charlie(0)"]


def test_transfer_receiver_outgoing_unchanged():
    # bob RECEIVES a transfer — only sender's outgoing increases
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "500"],
        ["TRANSFER",       "4", "alice", "bob", "200"],
        ["TOP_SPENDERS",   "5", "2"],
    ]
    # alice: 200 outgoing (sent 200), bob: 0 (received 200, didn't send anything)
    assert solution(queries) == ["true", "true", "500", "300", "alice(200), bob(0)"]


def test_worked_example_from_spec():
    # Matches the exact worked example in level2.md
    queries = [
        ["CREATE_ACCOUNT", "1",  "alice"],
        ["CREATE_ACCOUNT", "2",  "bob"],
        ["CREATE_ACCOUNT", "3",  "carol"],
        ["DEPOSIT",        "4",  "alice", "500"],
        ["DEPOSIT",        "5",  "bob",   "300"],
        ["PAY",            "6",  "alice", "200"],
        ["TRANSFER",       "7",  "alice", "bob", "100"],
        ["TRANSFER",       "8",  "carol", "alice", "50"],
        ["TRANSFER",       "9",  "alice", "alice", "50"],
        ["TOP_SPENDERS",   "10", "2"],
        ["TOP_SPENDERS",   "11", "5"],
    ]
    assert solution(queries) == [
        "true", "true", "true", "500", "300", "300", "200", "", "",
        "alice(300), bob(0)",
        "alice(300), bob(0), carol(0)",
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
