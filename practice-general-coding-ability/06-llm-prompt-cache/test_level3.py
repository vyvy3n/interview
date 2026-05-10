"""
Level 3 tests — run with: python test_level3.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_cache_put_with_ttl_basic_hit():
    queries = [
        ["CACHE_PUT_WITH_TTL", "1", "p", "r", "10"],
        ["CACHE_GET",          "5", "p"],
    ]
    assert solution(queries) == ["", "r"]


def test_ttl_boundary_expired_at_exactly_ts_plus_ttl():
    # Entry stored at ts=1 with ttl=9: expiry = 1+9 = 10.
    # At ts=10 the entry is EXPIRED (half-open: valid only for ts < 10).
    queries = [
        ["CACHE_PUT_WITH_TTL", "1", "p", "r", "9"],
        ["CACHE_GET",          "9", "p"],   # ts=9 < 10 → still live → hit
        ["CACHE_GET",         "10", "p"],   # ts=10 >= 10 → expired → miss
    ]
    assert solution(queries) == ["", "r", ""]


def test_ttl_boundary_one_before_expiry():
    # expiry = 5 + 5 = 10; ts=9 is still valid
    queries = [
        ["CACHE_PUT_WITH_TTL", "5", "p", "r", "5"],
        ["CACHE_GET",          "9", "p"],
    ]
    assert solution(queries) == ["", "r"]


def test_cache_delete_expired_returns_false():
    queries = [
        ["CACHE_PUT_WITH_TTL", "1", "p", "r", "5"],
        ["CACHE_DELETE",       "6", "p"],  # expiry=6, ts=6 → expired
    ]
    assert solution(queries) == ["", "false"]


def test_hit_count_expired_returns_empty():
    queries = [
        ["CACHE_PUT_WITH_TTL", "1",  "p", "r", "5"],
        ["CACHE_GET",          "3",  "p"],  # hit, count→1
        ["HIT_COUNT",          "6",  "p"],  # expired at ts=6 → ""
    ]
    assert solution(queries) == ["", "r", ""]


def test_plain_put_clears_ttl():
    # Put with TTL, then overwrite with plain PUT — should never expire
    queries = [
        ["CACHE_PUT_WITH_TTL", "1", "p", "r-ttl", "5"],
        ["CACHE_PUT",          "2", "p", "r-plain"],  # clears TTL
        ["CACHE_GET",          "6", "p"],              # ts=6 >= expiry=6 but TTL cleared → still live
        ["CACHE_GET",         "100", "p"],             # far future — still live
    ]
    assert solution(queries) == ["", "", "r-plain", "r-plain"]


def test_set_capacity_evicts_lru():
    queries = [
        ["CACHE_PUT",     "1", "A", "r"],
        ["CACHE_PUT",     "2", "B", "r"],
        ["CACHE_PUT",     "3", "C", "r"],
        ["SET_CAPACITY",  "4", "2"],  # 3 live → evict 1 LRU (A, la=1)
        ["CACHE_GET",     "5", "A"],  # evicted → miss
        ["CACHE_GET",     "6", "B"],  # still here
        ["CACHE_GET",     "7", "C"],  # still here
    ]
    assert solution(queries) == ["", "", "", "1", "", "r", "r"]


def test_set_capacity_no_eviction_needed():
    queries = [
        ["CACHE_PUT",    "1", "A", "r"],
        ["CACHE_PUT",    "2", "B", "r"],
        ["SET_CAPACITY", "3", "5"],  # already under cap
    ]
    assert solution(queries) == ["", "", "0"]


def test_set_capacity_expired_not_counted():
    # B is expired before SET_CAPACITY; only A is live
    queries = [
        ["CACHE_PUT_WITH_TTL", "1", "A", "r", "100"],
        ["CACHE_PUT_WITH_TTL", "2", "B", "r", "3"],   # expires at ts=5
        ["SET_CAPACITY",       "5", "1"],              # B expired; only A is live → no eviction
    ]
    assert solution(queries) == ["", "", "0"]


def test_cache_get_updates_last_access_for_lru():
    # Without GET: A(la=1), B(la=2), C(la=3). Capacity=2 → evict A.
    # With GET on A before SET_CAPACITY: A(la=4), B(la=2), C(la=3). Evict B (oldest la).
    queries = [
        ["CACHE_PUT",    "1", "A", "r"],
        ["CACHE_PUT",    "2", "B", "r"],
        ["CACHE_PUT",    "3", "C", "r"],
        ["CACHE_GET",    "4", "A"],           # A.last_access → 4 (now most recently used)
        ["SET_CAPACITY", "5", "2"],           # live: A(la=4), B(la=2), C(la=3) → evict B
        ["CACHE_GET",    "6", "A"],           # still here
        ["CACHE_GET",    "7", "B"],           # evicted → miss
        ["CACHE_GET",    "8", "C"],           # still here
    ]
    assert solution(queries) == ["", "", "", "r", "1", "r", "", "r"]


def test_new_put_evicts_lru_when_at_capacity():
    queries = [
        ["CACHE_PUT",    "1", "A", "r"],
        ["CACHE_PUT",    "2", "B", "r"],
        ["SET_CAPACITY", "3", "2"],  # no eviction, at capacity
        ["CACHE_PUT",    "4", "C", "r"],  # would exceed cap → evict A (la=1)
        ["CACHE_GET",    "5", "A"],       # evicted
        ["CACHE_GET",    "6", "B"],       # still here
        ["CACHE_GET",    "7", "C"],       # just added
    ]
    assert solution(queries) == ["", "", "0", "", "", "r", "r"]


def test_top_k_hot_excludes_expired():
    queries = [
        ["CACHE_PUT_WITH_TTL", "1", "A", "r", "5"],
        ["CACHE_PUT",          "2", "B", "r"],
        ["CACHE_GET",          "3", "A"],
        ["CACHE_GET",          "4", "B"],
        ["TOP_K_HOT",          "6", "3"],  # A expired at ts=6 → only B visible
    ]
    assert solution(queries) == ["", "", "r", "r", "B(1)"]


def test_worked_example_from_spec():
    queries = [
        ["CACHE_PUT_WITH_TTL", "1",  "A", "resp-A", "10"],
        ["CACHE_PUT_WITH_TTL", "2",  "B", "resp-B", "5"],
        ["CACHE_PUT",          "3",  "C", "resp-C"],
        ["SET_CAPACITY",       "4",  "2"],
        ["CACHE_GET",          "5",  "A"],
        ["CACHE_GET",          "7",  "B"],
        ["CACHE_GET",          "9",  "A"],
        ["CACHE_PUT",          "10", "D", "resp-D"],
        ["CACHE_GET",          "11", "A"],
        ["CACHE_GET",          "12", "C"],
    ]
    assert solution(queries) == ["", "", "", "1", "", "", "", "", "", "resp-C"]


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
