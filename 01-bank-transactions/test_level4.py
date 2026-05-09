"""
Level 4 tests — run with: python test_level4.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_merge_basic():
    # Merge bob into alice: balances combine, bob disappears
    queries = [
        ["CREATE_ACCOUNT",  "1", "alice"],
        ["CREATE_ACCOUNT",  "2", "bob"],
        ["DEPOSIT",         "3", "alice", "300"],
        ["DEPOSIT",         "4", "bob",   "200"],
        ["MERGE_ACCOUNTS",  "5", "alice", "bob"],
    ]
    assert solution(queries) == ["true", "true", "300", "200", "true"]


def test_merge_missing_id1():
    # id1 doesn't exist → ""
    queries = [
        ["CREATE_ACCOUNT", "1", "bob"],
        ["DEPOSIT",        "2", "bob", "100"],
        ["MERGE_ACCOUNTS", "3", "ghost", "bob"],
    ]
    assert solution(queries) == ["true", "100", ""]


def test_merge_missing_id2():
    # id2 doesn't exist → ""
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT",        "2", "alice", "100"],
        ["MERGE_ACCOUNTS", "3", "alice", "ghost"],
    ]
    assert solution(queries) == ["true", "100", ""]


def test_merge_same_id():
    # id1 == id2 → "" even if account exists
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["DEPOSIT",        "2", "alice", "100"],
        ["MERGE_ACCOUNTS", "3", "alice", "alice"],
    ]
    assert solution(queries) == ["true", "100", ""]


def test_merge_balance_combines():
    # After merge, id1 has sum of both balances
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "400"],
        ["DEPOSIT",        "4", "bob",   "600"],
        ["MERGE_ACCOUNTS", "5", "alice", "bob"],
        ["PAY",            "6", "alice", "100"],    # alice now has 1000; 1000-100=900
    ]
    assert solution(queries) == ["true", "true", "400", "600", "true", "900"]


def test_merge_id2_ceases_to_exist():
    # After merge, operations on id2 return error
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "bob", "100"],
        ["MERGE_ACCOUNTS", "4", "alice", "bob"],
        ["DEPOSIT",        "5", "bob",   "999"],     # bob is gone → ""
        ["PAY",            "6", "bob",   "10"],      # bob is gone → ""
        ["TRANSFER",       "7", "alice", "bob", "50"],  # to bob is gone → ""
        ["TRANSFER",       "8", "bob",   "alice", "50"],  # from bob is gone → ""
    ]
    assert solution(queries) == ["true", "true", "100", "true", "", "", "", ""]


def test_merge_outgoing_combines_for_top_spenders():
    # alice outgoing=50, bob outgoing=100; after merge alice shows 150
    queries = [
        ["CREATE_ACCOUNT", "1",  "alice"],
        ["CREATE_ACCOUNT", "2",  "bob"],
        ["DEPOSIT",        "3",  "alice", "500"],
        ["DEPOSIT",        "4",  "bob",   "500"],
        ["PAY",            "5",  "alice", "50"],    # alice outgoing=50
        ["PAY",            "6",  "bob",   "100"],   # bob outgoing=100
        ["MERGE_ACCOUNTS", "7",  "alice", "bob"],
        ["TOP_SPENDERS",   "8",  "2"],              # alice(150); only alice exists
    ]
    assert solution(queries) == ["true", "true", "500", "500", "450", "400", "true", "alice(150)"]


def test_merge_pending_payment_transfers_to_id1():
    # bob has a pending payment; after merge it fires from alice's balance
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["CREATE_ACCOUNT",   "2",  "bob"],
        ["DEPOSIT",          "3",  "alice", "400"],
        ["DEPOSIT",          "4",  "bob",   "200"],
        ["SCHEDULE_PAYMENT", "5",  "bob",   "100", "10"],  # payment1, fires at ts=15
        ["MERGE_ACCOUNTS",   "6",  "alice", "bob"],         # bob's payment1 → alice's; alice bal=400+200=600
        ["PAY",              "20", "alice", "1"],            # at ts=20: payment1 fires (alice: 600-100=500), then PAY (500-1=499)
    ]
    assert solution(queries) == ["true", "true", "400", "200", "payment1", "true", "499"]


def test_cancel_inherited_payment_via_id1():
    # After merge, CANCEL_PAYMENT for bob's payment must be issued against alice
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["CREATE_ACCOUNT",   "2",  "bob"],
        ["DEPOSIT",          "3",  "alice", "400"],
        ["DEPOSIT",          "4",  "bob",   "200"],
        ["SCHEDULE_PAYMENT", "5",  "bob",   "100", "20"],  # payment1, fires at ts=25
        ["MERGE_ACCOUNTS",   "6",  "alice", "bob"],
        ["CANCEL_PAYMENT",   "7",  "alice", "payment1"],   # alice now owns payment1 → "true"
        ["PAY",              "30", "alice", "1"],           # payment1 cancelled; alice bal=600; 600-1=599
    ]
    assert solution(queries) == ["true", "true", "400", "200", "payment1", "true", "true", "599"]


def test_cancel_inherited_payment_via_old_id_fails():
    # After merge, CANCEL on bob's name fails (bob is gone)
    queries = [
        ["CREATE_ACCOUNT",   "1", "alice"],
        ["CREATE_ACCOUNT",   "2", "bob"],
        ["DEPOSIT",          "3", "bob", "200"],
        ["SCHEDULE_PAYMENT", "4", "bob", "100", "20"],  # payment1
        ["MERGE_ACCOUNTS",   "5", "alice", "bob"],
        ["CANCEL_PAYMENT",   "6", "bob", "payment1"],   # bob gone → ""
    ]
    assert solution(queries) == ["true", "true", "200", "payment1", "true", ""]


def test_merge_fires_due_payments_before_merging():
    # bob has payment1 due at ts=5; MERGE at ts=5 fires payment1 from bob's balance first
    # bob: 200 - 100 (payment1 fires) = 100; then merge: alice=300+100=400
    queries = [
        ["CREATE_ACCOUNT",   "1", "alice"],
        ["CREATE_ACCOUNT",   "2", "bob"],
        ["DEPOSIT",          "3", "alice", "300"],
        ["DEPOSIT",          "4", "bob",   "200"],
        ["SCHEDULE_PAYMENT", "4", "bob",   "100", "1"],   # payment1, fires at ts=5
        ["MERGE_ACCOUNTS",   "5", "alice", "bob"],         # fires payment1 first, then merges
        ["PAY",              "6", "alice", "1"],            # alice=300+100=400; 400-1=399
    ]
    # At ts=5 (MERGE query): payment1 (execute_time=5) fires before merge.
    # bob: 200-100=100. Then merge: alice.bal=300+100=400. alice.out=0+0+100=100 (payment1 fired counts).
    assert solution(queries) == ["true", "true", "300", "200", "payment1", "true", "399"]


def test_merge_fired_payment_outgoing_goes_to_id1():
    # Payment fired during merge (from bob's balance before merge) → counted in alice's outgoing after merge
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["CREATE_ACCOUNT",   "2",  "bob"],
        ["DEPOSIT",          "3",  "alice", "300"],
        ["DEPOSIT",          "4",  "bob",   "200"],
        ["SCHEDULE_PAYMENT", "4",  "bob",   "100", "1"],  # payment1, fires at ts=5
        ["MERGE_ACCOUNTS",   "5",  "alice", "bob"],
        ["TOP_SPENDERS",     "6",  "1"],                   # alice outgoing should include the fired payment
    ]
    # payment1 fires from bob before merge (bob outgoing+=100); merge: alice.out=0+100=100
    assert solution(queries) == ["true", "true", "300", "200", "payment1", "true", "alice(100)"]


def test_merge_then_top_spenders_only_shows_id1():
    # bob disappears from TOP_SPENDERS after merge
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "alice", "300"],
        ["DEPOSIT",        "4", "bob",   "200"],
        ["PAY",            "5", "bob",   "50"],    # bob outgoing=50
        ["TOP_SPENDERS",   "6", "2"],               # bob(50), alice(0)
        ["MERGE_ACCOUNTS", "7", "alice", "bob"],
        ["TOP_SPENDERS",   "8", "2"],               # only alice(50) — bob gone
    ]
    assert solution(queries) == ["true", "true", "300", "200", "150", "bob(50), alice(0)", "true", "alice(50)"]


def test_sequential_merges():
    # A←B then A←C — both merges work, all state accumulates in A
    queries = [
        ["CREATE_ACCOUNT", "1",  "alice"],
        ["CREATE_ACCOUNT", "2",  "bob"],
        ["CREATE_ACCOUNT", "3",  "carol"],
        ["DEPOSIT",        "4",  "alice", "100"],
        ["DEPOSIT",        "5",  "bob",   "200"],
        ["DEPOSIT",        "6",  "carol", "300"],
        ["PAY",            "7",  "alice", "10"],   # alice out=10
        ["PAY",            "8",  "bob",   "20"],   # bob out=20
        ["PAY",            "9",  "carol", "30"],   # carol out=30
        ["MERGE_ACCOUNTS", "10", "alice", "bob"],  # alice bal=90+180=270, out=10+20=30
        ["MERGE_ACCOUNTS", "11", "alice", "carol"],  # alice bal=270+270=540, out=30+30=60
        ["TOP_SPENDERS",   "12", "3"],               # only alice(60)
    ]
    assert solution(queries) == [
        "true", "true", "true", "100", "200", "300", "90", "180", "270", "true", "true", "alice(60)",
    ]


def test_merge_create_account_duplicate_after_merge():
    # After bob is merged into alice, CREATE_ACCOUNT bob → "true" (new account)
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CREATE_ACCOUNT", "2", "bob"],
        ["DEPOSIT",        "3", "bob", "100"],
        ["MERGE_ACCOUNTS", "4", "alice", "bob"],
        ["CREATE_ACCOUNT", "5", "bob"],   # bob is gone, create fresh → "true"
        ["DEPOSIT",        "6", "bob", "999"],
        ["TOP_SPENDERS",   "7", "2"],    # alice(0), new bob(0) — alice merged bob's outgoing (0+0=0)
    ]
    assert solution(queries) == ["true", "true", "100", "true", "true", "999", "alice(0), bob(0)"]


def test_worked_example_from_spec():
    # Matches the worked example in level4.md exactly
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["CREATE_ACCOUNT",   "2",  "bob"],
        ["DEPOSIT",          "3",  "alice", "300"],
        ["DEPOSIT",          "4",  "bob",   "200"],
        ["PAY",              "5",  "bob",   "50"],
        ["SCHEDULE_PAYMENT", "6",  "bob",   "100", "10"],  # payment1, fires at ts=16
        ["TRANSFER",         "7",  "alice", "bob", "50"],
        ["TOP_SPENDERS",     "8",  "2"],
        ["MERGE_ACCOUNTS",   "9",  "alice", "bob"],
        ["TOP_SPENDERS",     "10", "2"],
        ["DEPOSIT",          "11", "bob",   "999"],
        ["CANCEL_PAYMENT",   "12", "alice", "payment1"],
        ["TOP_SPENDERS",     "20", "2"],
    ]
    assert solution(queries) == [
        "true", "true", "300", "200", "150", "payment1", "250",
        "alice(50), bob(50)",
        "true",
        "alice(100)",
        "",
        "true",
        "alice(100)",
    ]


def test_l1_l2_l3_still_work_after_merge():
    # Integration: all prior-level ops work correctly post-merge
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["CREATE_ACCOUNT",   "2",  "bob"],
        ["DEPOSIT",          "3",  "alice", "500"],
        ["DEPOSIT",          "4",  "bob",   "300"],
        ["SCHEDULE_PAYMENT", "5",  "bob",   "50", "15"],  # payment1, fires at ts=20
        ["PAY",              "6",  "alice", "100"],        # alice out=100
        ["TRANSFER",         "7",  "alice", "bob", "50"], # alice out=150, bob bal=350
        ["MERGE_ACCOUNTS",   "8",  "alice", "bob"],
        # After merge: alice.bal=350+350=700 (alice had 350, bob had 350), alice.out=150+0=150
        # Wait, let me re-trace:
        # alice after PAY: 500-100=400, out=100
        # alice after TRANSFER to bob: 400-50=350, out=150
        # bob after DEPOSIT: 300, after receiving transfer: 300+50=350, out=0
        # MERGE at ts=8: no payments due (payment1 fires at ts=20). alice.bal=350+350=700, alice.out=150+0=150
        ["DEPOSIT",          "9",  "alice", "100"],        # alice: 700+100=800
        ["PAY",              "10", "alice", "50"],          # alice: 800-50=750, alice.out=200
        ["SCHEDULE_PAYMENT", "11", "alice", "100", "5"],   # payment2, fires at ts=16
        ["TOP_SPENDERS",     "17", "1"],                    # ts=17: payment2 fires at ts=16 (fires before ts=17 query); alice.out=200+100=300. payment1 at ts=20 not yet due.
        ["CANCEL_PAYMENT",   "18", "alice", "payment1"],   # payment1 (inherited from bob) still pending (ts=20 > 18) → "true"
        ["TOP_SPENDERS",     "25", "1"],                    # ts=25: payment1 was cancelled, nothing fires. alice.out=300
    ]
    assert solution(queries) == [
        "true", "true", "500", "300", "payment1", "400", "350", "true",
        "800", "750", "payment2", "alice(300)", "true", "alice(300)",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 4 complete — you've built the full bank!")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
