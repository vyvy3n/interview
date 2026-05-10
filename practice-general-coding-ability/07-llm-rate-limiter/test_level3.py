"""
Level 3 tests — run with: python test_level3.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_no_refill_rate_bucket_stays_static():
    """Without SET_REFILL_RATE, the bucket should not grow over time."""
    queries = [
        ["REGISTER_KEY",  "0",  "key-A", "1000"],
        ["CONSUME",       "0",  "key-A", "600"],
        ["GET_REMAINING", "100","key-A"],   # 100 seconds later — still 400
    ]
    assert solution(queries) == ["true", "400", "400"]


def test_set_refill_rate_missing_key_returns_false():
    queries = [["SET_REFILL_RATE", "1", "ghost", "100"]]
    assert solution(queries) == ["false"]


def test_set_refill_rate_returns_true():
    queries = [
        ["REGISTER_KEY",   "1", "key-A", "1000"],
        ["SET_REFILL_RATE","2", "key-A", "50"],
    ]
    assert solution(queries) == ["true", "true"]


def test_refill_applied_on_get_remaining():
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "600"],
        ["SET_REFILL_RATE","0",  "key-A", "50"],
        ["GET_REMAINING",  "10", "key-A"],  # elapsed=10, +50*10=500 → 400+500=900
    ]
    assert solution(queries) == ["true", "400", "true", "900"]


def test_refill_capped_at_max():
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "200"],
        ["SET_REFILL_RATE","0",  "key-A", "100"],
        ["GET_REMAINING",  "100","key-A"],  # elapsed=100, +100*100=10000 → 800+10000=10800, cap at 1000
    ]
    assert solution(queries) == ["true", "800", "true", "1000"]


def test_refill_across_multiple_operations():
    """Each operation should only refill elapsed time since last_action_ts."""
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "600"],
        ["SET_REFILL_RATE","0",  "key-A", "50"],
        ["GET_REMAINING",  "4",  "key-A"],  # elapsed=4, +50*4=200 → 400+200=600
        ["GET_REMAINING",  "6",  "key-A"],  # elapsed=2, +50*2=100 → 600+100=700
        ["GET_REMAINING",  "10", "key-A"],  # elapsed=4, +50*4=200 → 700+200=900
    ]
    assert solution(queries) == ["true", "400", "true", "600", "700", "900"]


def test_set_refill_rate_uses_old_rate_first():
    """SET_REFILL_RATE must refill with OLD rate before applying new rate."""
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "600"],   # tokens=400
        ["SET_REFILL_RATE","0",  "key-A", "50"],    # rate=50, last_ts=0
        ["GET_REMAINING",  "5",  "key-A"],           # +50*5=250 → 650, last_ts=5
        # now change rate: old rate=50, elapsed=5, +50*5=250 → 650+250=900
        ["SET_REFILL_RATE","10", "key-A", "10"],    # old rate refill first: +50*5=250 → 900
        ["GET_REMAINING",  "20", "key-A"],           # new rate=10, elapsed=10, +10*10=100 → 1000, cap
    ]
    assert solution(queries) == ["true", "400", "true", "650", "true", "1000"]


def test_total_consumed_triggers_refill_update():
    """TOTAL_CONSUMED should update last_action_ts (via apply_refill)."""
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "600"],   # tokens=400, total=600
        ["SET_REFILL_RATE","0",  "key-A", "100"],   # rate=100, last_ts=0
        ["TOTAL_CONSUMED", "5",  "key-A"],           # refills: +100*5=500 → 900, last_ts=5; total=600
        # If last_ts was NOT updated by TOTAL_CONSUMED, next op would double-count elapsed time
        ["GET_REMAINING",  "10", "key-A"],           # elapsed=5 (not 10), +100*5=500 → 1000 cap
    ]
    assert solution(queries) == ["true", "400", "true", "600", "1000"]


def test_refill_zero_rate_never_fills():
    """rate=0 means no refill. Explicitly setting rate=0 (if re-set) keeps bucket static."""
    queries = [
        ["REGISTER_KEY",   "0",   "key-A", "500"],
        ["SET_REFILL_RATE","0",   "key-A", "100"],
        ["CONSUME",        "0",   "key-A", "300"],   # tokens=200
        ["SET_REFILL_RATE","5",   "key-A", "0"],     # old rate=100, elapsed=5, +100*5=500 → 700 cap at 500; new rate=0
        ["GET_REMAINING",  "1000","key-A"],            # elapsed=995, +0*995=0 → still 500
    ]
    # After SET_REFILL_RATE at ts=5: refill 100*5=500 → 200+500=700 cap at 500.
    # After new rate=0 set, 1000 seconds pass — no refill.
    assert solution(queries) == ["true", "true", "200", "true", "500"]


def test_consume_after_refill():
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "800"],
        ["SET_REFILL_RATE","0",  "key-A", "50"],
        ["CONSUME",        "10", "key-A", "300"],   # refill: +50*10=500 → 200+500=700; consume 300 → 400
    ]
    assert solution(queries) == ["true", "200", "true", "400"]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_KEY",    "0",   "key-A", "1000"],
        ["CONSUME",         "0",   "key-A", "600"],
        ["SET_REFILL_RATE",  "5",  "key-A", "50"],
        ["GET_REMAINING",   "7",   "key-A"],
        ["CONSUME",         "10",  "key-A", "500"],
        ["SET_REFILL_RATE",  "10", "key-A", "100"],
        ["GET_REMAINING",   "15",  "key-A"],
        ["CONSUME",         "20",  "key-A", "2000"],
        ["GET_REMAINING",   "20",  "key-A"],
    ]
    assert solution(queries) == [
        "true", "400", "true", "500", "150", "true", "650", "", "1000",
    ]


def test_same_timestamp_zero_elapsed():
    """Multiple ops at the same ts — elapsed=0 means zero refill."""
    queries = [
        ["REGISTER_KEY",   "5", "key-A", "1000"],
        ["SET_REFILL_RATE","5", "key-A", "500"],
        ["CONSUME",        "5", "key-A", "200"],
        ["GET_REMAINING",  "5", "key-A"],   # elapsed=0 each time → no refill
    ]
    assert solution(queries) == ["true", "true", "800", "800"]


def test_top_k_consumers_unaffected_by_refill():
    """TOP_K_CONSUMERS still ranks by total_consumed, not bucket level."""
    queries = [
        ["REGISTER_KEY",    "0",  "key-A", "1000"],
        ["REGISTER_KEY",    "0",  "key-B", "1000"],
        ["SET_REFILL_RATE",  "0", "key-A", "100"],
        ["CONSUME",         "0",  "key-A", "800"],  # total_consumed key-A=800
        ["CONSUME",         "0",  "key-B", "600"],  # total_consumed key-B=600
        ["TOP_K_CONSUMERS", "100","2"],              # ranking by consumed, not bucket level
    ]
    assert solution(queries) == ["true", "true", "true", "200", "400", "key-A(800), key-B(600)"]


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
