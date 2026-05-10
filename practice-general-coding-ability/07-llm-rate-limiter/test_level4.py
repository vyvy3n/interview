"""
Level 4 tests — run with: python test_level4.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


# ── UPGRADE_TIER tests ──────────────────────────────────────────────────────


def test_upgrade_tier_missing_key_returns_empty():
    queries = [["UPGRADE_TIER", "1", "ghost", "2000", "100"]]
    assert solution(queries) == [""]


def test_upgrade_tier_basic():
    """Upgrade with no prior refill to worry about."""
    queries = [
        ["REGISTER_KEY",  "0", "key-A", "1000"],
        ["CONSUME",       "0", "key-A", "400"],   # tokens=600
        ["UPGRADE_TIER",  "0", "key-A", "2000", "100"],
    ]
    # elapsed=0, no refill. max→2000, tokens=600 ≤ 2000, rate→100. Return 600.
    assert solution(queries) == ["true", "600", "600"]


def test_upgrade_tier_refills_with_old_rate_before_expanding():
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "600"],   # tokens=400
        ["SET_REFILL_RATE","0",  "key-A", "50"],    # rate=50, last_ts=0
        ["UPGRADE_TIER",   "10", "key-A", "2000", "200"],
    ]
    # Refill: elapsed=10, +50*10=500 → 400+500=900, cap at OLD max=1000 → 900.
    # max→2000, tokens=900 ≤ 2000. rate→200. Return 900.
    assert solution(queries) == ["true", "400", "true", "900"]


def test_upgrade_tier_caps_tokens_to_new_max_if_smaller():
    """If new_max < current_tokens after refill, tokens must be capped."""
    queries = [
        ["REGISTER_KEY",   "0", "key-A", "1000"],
        ["UPGRADE_TIER",   "0", "key-A", "300", "50"],
    ]
    # elapsed=0, no refill. tokens=1000 > new_max=300 → cap to 300. rate→50. Return 300.
    assert solution(queries) == ["true", "300"]


def test_upgrade_tier_refill_capped_at_old_max_not_new():
    """The refill step caps at OLD max, not new_max."""
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["CONSUME",        "0",  "key-A", "200"],   # tokens=800
        ["SET_REFILL_RATE","0",  "key-A", "100"],   # rate=100
        # At ts=10: refill 100*10=1000 → 800+1000=1800 capped at OLD max=1000. Then max→3000.
        ["UPGRADE_TIER",   "10", "key-A", "3000", "200"],
    ]
    assert solution(queries) == ["true", "800", "true", "1000"]


def test_upgrade_tier_then_get_remaining_uses_new_rate():
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "500"],
        ["CONSUME",        "0",  "key-A", "300"],   # tokens=200
        ["SET_REFILL_RATE","0",  "key-A", "10"],    # rate=10
        ["UPGRADE_TIER",   "0",  "key-A", "2000", "100"],  # elapsed=0, no refill. max→2000, rate→100
        ["GET_REMAINING",  "5",  "key-A"],           # elapsed=5, +100*5=500 → 700
    ]
    assert solution(queries) == ["true", "200", "true", "200", "700"]


# ── MERGE_KEYS tests ─────────────────────────────────────────────────────────


def test_merge_self_returns_empty():
    queries = [
        ["REGISTER_KEY", "0", "key-A", "1000"],
        ["MERGE_KEYS",   "1", "key-A", "key-A"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_missing_surviving_key():
    queries = [
        ["REGISTER_KEY", "0", "key-B", "500"],
        ["MERGE_KEYS",   "1", "ghost", "key-B"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_missing_absorbed_key():
    queries = [
        ["REGISTER_KEY", "0", "key-A", "1000"],
        ["MERGE_KEYS",   "1", "key-A", "ghost"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_basic_no_refill():
    queries = [
        ["REGISTER_KEY",  "0", "key-A", "1000"],
        ["REGISTER_KEY",  "0", "key-B", "500"],
        ["CONSUME",       "0", "key-A", "200"],   # key-A: tokens=800, total=200
        ["CONSUME",       "0", "key-B", "100"],   # key-B: tokens=400, total=100
        ["MERGE_KEYS",    "0", "key-A", "key-B"],
    ]
    # No refill (elapsed=0 for both). max=1500, tokens=1200, total=300. Return "true".
    assert solution(queries) == ["true", "true", "800", "400", "true"]


def test_merge_absorbed_key_gone_after_merge():
    queries = [
        ["REGISTER_KEY",  "0", "key-A", "1000"],
        ["REGISTER_KEY",  "0", "key-B", "500"],
        ["MERGE_KEYS",    "0", "key-A", "key-B"],
        ["GET_REMAINING", "0", "key-B"],   # absorbed — must return ""
        ["CONSUME",       "0", "key-B", "10"],  # absorbed — must return ""
    ]
    assert solution(queries) == ["true", "true", "true", "", ""]


def test_merge_surviving_key_gets_combined_max_and_tokens():
    queries = [
        ["REGISTER_KEY",  "0", "key-A", "1000"],
        ["REGISTER_KEY",  "0", "key-B", "800"],
        ["CONSUME",       "0", "key-A", "300"],   # key-A tokens=700
        ["CONSUME",       "0", "key-B", "200"],   # key-B tokens=600
        ["MERGE_KEYS",    "0", "key-A", "key-B"],
        ["GET_REMAINING", "0", "key-A"],
    ]
    # max=1800, tokens=700+600=1300 ≤ 1800. Return 1300.
    assert solution(queries) == ["true", "true", "700", "600", "true", "1300"]


def test_merge_total_consumed_is_sum():
    queries = [
        ["REGISTER_KEY",   "0", "key-A", "5000"],
        ["REGISTER_KEY",   "0", "key-B", "5000"],
        ["CONSUME",        "0", "key-A", "1000"],
        ["CONSUME",        "0", "key-B", "2500"],
        ["MERGE_KEYS",     "0", "key-A", "key-B"],
        ["TOTAL_CONSUMED", "0", "key-A"],
    ]
    assert solution(queries) == ["true", "true", "4000", "2500", "true", "3500"]


def test_merge_refill_rate_is_max_not_sum():
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["REGISTER_KEY",   "0",  "key-B", "1000"],
        ["SET_REFILL_RATE","0",  "key-A", "30"],
        ["SET_REFILL_RATE","0",  "key-B", "80"],
        ["MERGE_KEYS",     "0",  "key-A", "key-B"],
        # Surviving key's rate should be max(30, 80) = 80 (not 110)
        ["CONSUME",        "0",  "key-A", "2000"],  # full bucket = 2000, consume 2000 → 0
        ["GET_REMAINING",  "10", "key-A"],  # elapsed=10, +80*10=800 → 800 (not 1100)
    ]
    assert solution(queries) == ["true", "true", "true", "true", "true", "0", "800"]


def test_merge_refill_applied_before_merge():
    """Both keys should be refilled to the merge timestamp before combining."""
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["REGISTER_KEY",   "0",  "key-B", "500"],
        ["SET_REFILL_RATE","0",  "key-A", "100"],
        ["SET_REFILL_RATE","0",  "key-B", "40"],
        ["CONSUME",        "0",  "key-A", "200"],   # key-A tokens=800
        ["CONSUME",        "0",  "key-B", "100"],   # key-B tokens=400
        ["MERGE_KEYS",     "10", "key-A", "key-B"],
        ["GET_REMAINING",  "10", "key-A"],
    ]
    # key-A refill: elapsed=10, +100*10=1000 → 800+1000=1800, cap at 1000 → 1000
    # key-B refill: elapsed=10, +40*10=400 → 400+400=800, cap at 500 → 500
    # max=1500, tokens=1000+500=1500 → cap at 1500 → 1500
    # GET_REMAINING at ts=10: elapsed=0 → 1500
    assert solution(queries) == ["true", "true", "true", "true", "800", "400", "true", "1500"]


def test_merge_combined_tokens_capped_at_combined_max():
    """If surviving+absorbed tokens > combined max, cap at combined max."""
    queries = [
        ["REGISTER_KEY",  "0", "key-A", "600"],
        ["REGISTER_KEY",  "0", "key-B", "600"],
        # Neither key has consumed any — both are full (600 each)
        ["MERGE_KEYS",    "0", "key-A", "key-B"],
        ["GET_REMAINING", "0", "key-A"],
    ]
    # max=1200, tokens=600+600=1200 ≤ 1200. No cap needed.
    assert solution(queries) == ["true", "true", "true", "1200"]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_KEY",   "0",  "key-A", "1000"],
        ["REGISTER_KEY",   "0",  "key-B", "500"],
        ["SET_REFILL_RATE","0",  "key-A", "100"],
        ["SET_REFILL_RATE","0",  "key-B", "40"],
        ["CONSUME",        "0",  "key-A", "200"],
        ["CONSUME",        "0",  "key-B", "100"],
        ["MERGE_KEYS",     "10", "key-A", "key-B"],
        ["GET_REMAINING",  "10", "key-A"],
        ["GET_REMAINING",  "10", "key-B"],
        ["UPGRADE_TIER",   "20", "key-A", "3000", "200"],
        ["GET_REMAINING",  "25", "key-A"],
    ]
    # After MERGE at ts=10:
    #   key-A: elapsed=10, +100*10=1000 → 800+1000=1800 cap at 1000 → 1000
    #   key-B: elapsed=10, +40*10=400  → 400+400=800   cap at 500  → 500
    #   max=1500, tokens=1500, rate=max(100,40)=100, total=300
    # UPGRADE_TIER at ts=20: elapsed=10, +100*10=1000 → 1500+1000=2500, cap OLD max=1500 → 1500
    #   new max=3000, tokens=1500 ≤ 3000. rate=200. Return 1500.
    # GET_REMAINING at ts=25: elapsed=5, +200*5=1000 → 1500+1000=2500 ≤ 3000. Return 2500.
    assert solution(queries) == [
        "true", "true", "true", "true", "800", "400",
        "true", "1500", "", "1500", "2500",
    ]


def test_ops_on_absorbed_key_after_merge_return_false_or_empty():
    queries = [
        ["REGISTER_KEY",   "0", "key-A", "1000"],
        ["REGISTER_KEY",   "0", "key-B", "500"],
        ["MERGE_KEYS",     "0", "key-A", "key-B"],
        ["SET_REFILL_RATE","1", "key-B", "100"],    # absorbed — "false"
        ["UPGRADE_TIER",   "2", "key-B", "9999", "999"],  # absorbed — ""
        ["TOTAL_CONSUMED", "3", "key-B"],             # absorbed — ""
    ]
    assert solution(queries) == ["true", "true", "true", "false", "", ""]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 4 complete — you built Anthropic's rate limiter!")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
