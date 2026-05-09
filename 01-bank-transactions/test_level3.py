"""
Level 3 tests — run with: python test_level3.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_schedule_payment_basic():
    # Schedule and let it fire naturally; at ts=10 (delay=5 from ts=5), it fires
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "500"],
        ["SCHEDULE_PAYMENT", "5",  "alice", "200", "5"],   # fires at ts=10
        ["DEPOSIT",          "11", "alice", "0"],           # ts=11 > 10, payment should have fired
    ]
    # DEPOSIT 0 is invalid per spec. Use a PAY instead to observe balance.
    # Actually the spec says amount > 0. Observe balance via a PAY that returns new bal.
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "500"],
        ["SCHEDULE_PAYMENT", "5",  "alice", "200", "5"],   # fires at ts=10
        ["PAY",              "11", "alice", "1"],           # fires payment first (ts=10<=11), then PAY 1; alice: 500-200-1=299
    ]
    assert solution(queries) == ["true", "500", "payment1", "299"]


def test_schedule_payment_missing_account():
    # Scheduling on a nonexistent account → "" and counter doesn't increment
    queries = [
        ["SCHEDULE_PAYMENT", "1", "ghost", "100", "5"],    # account missing → ""
        ["CREATE_ACCOUNT",   "2", "alice"],
        ["DEPOSIT",          "3", "alice", "500"],
        ["SCHEDULE_PAYMENT", "4", "alice", "100", "5"],    # should be payment1 (counter not incremented by failed schedule)
    ]
    assert solution(queries) == ["", "true", "500", "payment1"]


def test_schedule_payment_counter_is_global():
    # Global counter: payment IDs are sequential across accounts
    queries = [
        ["CREATE_ACCOUNT",   "1", "alice"],
        ["CREATE_ACCOUNT",   "2", "bob"],
        ["DEPOSIT",          "3", "alice", "500"],
        ["DEPOSIT",          "4", "bob",   "500"],
        ["SCHEDULE_PAYMENT", "5", "alice", "100", "100"],
        ["SCHEDULE_PAYMENT", "6", "bob",   "200", "100"],
        ["SCHEDULE_PAYMENT", "7", "alice", "50",  "100"],
    ]
    assert solution(queries) == ["true", "true", "500", "500", "payment1", "payment2", "payment3"]


def test_cancel_payment_basic():
    # Cancel a pending payment before it fires
    queries = [
        ["CREATE_ACCOUNT",   "1", "alice"],
        ["DEPOSIT",          "2", "alice", "500"],
        ["SCHEDULE_PAYMENT", "3", "alice", "200", "10"],   # fires at ts=13
        ["CANCEL_PAYMENT",   "5", "alice", "payment1"],    # ts=5 < 13, not yet fired → "true"
        ["PAY",              "20", "alice", "1"],           # ts=20 > 13 but payment cancelled, so alice still has 500; 500-1=499
    ]
    assert solution(queries) == ["true", "500", "payment1", "true", "499"]


def test_cancel_payment_missing_account():
    # Cancel on a nonexistent account → ""
    queries = [
        ["CREATE_ACCOUNT",   "1", "alice"],
        ["DEPOSIT",          "2", "alice", "500"],
        ["SCHEDULE_PAYMENT", "3", "alice", "100", "10"],
        ["CANCEL_PAYMENT",   "4", "ghost", "payment1"],    # account missing → ""
    ]
    assert solution(queries) == ["true", "500", "payment1", ""]


def test_cancel_payment_wrong_account():
    # payment1 belongs to alice, bob tries to cancel it → ""
    queries = [
        ["CREATE_ACCOUNT",   "1", "alice"],
        ["CREATE_ACCOUNT",   "2", "bob"],
        ["DEPOSIT",          "3", "alice", "500"],
        ["SCHEDULE_PAYMENT", "4", "alice", "100", "10"],   # payment1 belongs to alice
        ["CANCEL_PAYMENT",   "5", "bob",   "payment1"],    # bob doesn't own it → ""
        ["CANCEL_PAYMENT",   "6", "alice", "payment1"],    # alice does → "true"
    ]
    assert solution(queries) == ["true", "true", "500", "payment1", "", "true"]


def test_cancel_payment_already_fired():
    # Payment fires at ts=10; cancel attempt at ts=11 → ""
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "500"],
        ["SCHEDULE_PAYMENT", "3",  "alice", "200", "7"],   # fires at ts=10
        ["CANCEL_PAYMENT",   "11", "alice", "payment1"],   # fires before ts=11 query → already fired → ""
    ]
    assert solution(queries) == ["true", "500", "payment1", ""]


def test_cancel_payment_nonexistent_id():
    # payment_id doesn't exist at all → ""
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],
        ["CANCEL_PAYMENT", "2", "alice", "payment99"],
    ]
    assert solution(queries) == ["true", ""]


def test_scheduled_payment_fires_at_exact_timestamp():
    # Payment execute_time == query timestamp → fires BEFORE the query
    # Schedule at ts=5 with delay=5 → fires at ts=10
    # At ts=10 PAY query: payment fires first, then PAY executes
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "300"],
        ["SCHEDULE_PAYMENT", "5",  "alice", "200", "5"],   # execute_time = 10
        ["PAY",              "10", "alice", "50"],          # payment fires (300-200=100), then PAY (100-50=50)
    ]
    assert solution(queries) == ["true", "300", "payment1", "50"]


def test_scheduled_payment_insufficient_funds_skipped_silently():
    # Payment fires but alice can't afford it → skipped, balance unchanged
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "100"],
        ["SCHEDULE_PAYMENT", "3",  "alice", "500", "5"],   # fires at ts=8; alice only has 100
        ["PAY",              "10", "alice", "50"],          # payment skipped; alice still 100; 100-50=50
    ]
    assert solution(queries) == ["true", "100", "payment1", "50"]


def test_scheduled_payment_fires_count_as_outgoing():
    # Fired scheduled payments count toward TOP_SPENDERS outgoing
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "500"],
        ["SCHEDULE_PAYMENT", "3",  "alice", "150", "5"],   # fires at ts=8
        ["TOP_SPENDERS",     "10", "1"],                    # payment fires before query; alice outgoing=150
    ]
    assert solution(queries) == ["true", "500", "payment1", "alice(150)"]


def test_multiple_payments_same_execute_time_fire_in_creation_order():
    # payment1 and payment2 both fire at ts=10; payment1 fires first
    # alice has 300: payment1=200 fires → alice=100; payment2=100 fires → alice=0
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "300"],
        ["SCHEDULE_PAYMENT", "3",  "alice", "200", "7"],   # payment1, fires at ts=10
        ["SCHEDULE_PAYMENT", "4",  "alice", "100", "6"],   # payment2, fires at ts=10
        ["PAY",              "11", "alice", "1"],           # both fired at ts=10; alice=0; PAY fails (insufficient)
    ]
    assert solution(queries) == ["true", "300", "payment1", "payment2", ""]


def test_multiple_payments_same_execute_time_first_drains_second_skipped():
    # payment1 fires first at ts=10 draining the account; payment2 also due ts=10 but insufficient → skipped
    # alice has 200: payment1=200 fires → alice=0; payment2=100 due but insufficient → skipped
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "200"],
        ["SCHEDULE_PAYMENT", "3",  "alice", "200", "7"],   # payment1, fires at ts=10
        ["SCHEDULE_PAYMENT", "4",  "alice", "100", "6"],   # payment2, fires at ts=10
        ["TOP_SPENDERS",     "11", "1"],                    # payment1 fired (outgoing=200), payment2 skipped
    ]
    assert solution(queries) == ["true", "200", "payment1", "payment2", "alice(200)"]


def test_schedule_fires_before_schedule_query():
    # A SCHEDULE_PAYMENT query at ts=15 triggers firing of earlier payments before registering new one
    # payment1 fires at ts=10, the SCHEDULE_PAYMENT query is at ts=15
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "500"],
        ["SCHEDULE_PAYMENT", "3",  "alice", "100", "7"],   # payment1, fires at ts=10
        ["SCHEDULE_PAYMENT", "15", "alice", "50",  "5"],   # at ts=15, payment1 fires first, then this registers
        ["TOP_SPENDERS",     "20", "1"],                    # payment2 (50) fires at ts=20
    ]
    # ts=15: payment1 fires (alice: 500-100=400), then payment2 registered (fires at ts=20)
    # ts=20: payment2 fires (alice: 400-50=350); alice outgoing=100+50=150
    assert solution(queries) == ["true", "500", "payment1", "payment2", "alice(150)"]


def test_worked_example_from_spec():
    # Matches the worked example in level3.md
    queries = [
        ["CREATE_ACCOUNT",   "1",  "alice"],
        ["DEPOSIT",          "2",  "alice", "500"],
        ["SCHEDULE_PAYMENT", "3",  "alice", "200", "5"],   # payment1, fires at ts=8
        ["SCHEDULE_PAYMENT", "4",  "alice", "100", "4"],   # payment2, fires at ts=8
        ["TOP_SPENDERS",     "6",  "1"],
        ["SCHEDULE_PAYMENT", "7",  "ghost", "50",  "1"],   # account missing → ""
        ["CANCEL_PAYMENT",   "8",  "alice", "payment2"],   # fires before ts=8: payment1 then payment2 both fire; payment2 already fired → ""
        ["TOP_SPENDERS",     "15", "1"],
        ["TOP_SPENDERS",     "20", "1"],
    ]
    assert solution(queries) == [
        "true", "500", "payment1", "payment2", "alice(0)", "", "", "alice(300)", "alice(300)",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 3 complete — commit and request Level 4.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
