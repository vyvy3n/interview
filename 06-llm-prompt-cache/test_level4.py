"""
Level 4 tests — run with: python test_level4.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_prefix_lookup_exact_match():
    queries = [
        ["CACHE_PUT",      "1", "hello", "world"],
        ["PREFIX_LOOKUP",  "2", "hello"],
    ]
    assert solution(queries) == ["", "hello"]


def test_prefix_lookup_longer_prompt():
    queries = [
        ["CACHE_PUT",     "1", "hello", "world"],
        ["PREFIX_LOOKUP", "2", "hello world how are you"],
    ]
    assert solution(queries) == ["", "hello"]


def test_prefix_lookup_no_match():
    queries = [
        ["CACHE_PUT",     "1", "hello", "world"],
        ["PREFIX_LOOKUP", "2", "goodbye"],
    ]
    assert solution(queries) == ["", ""]


def test_prefix_lookup_longest_wins():
    # Three cached entries are prefixes of the new prompt — longest wins
    queries = [
        ["CACHE_PUT",     "1", "You",                 "r1"],
        ["CACHE_PUT",     "2", "You are",             "r2"],
        ["CACHE_PUT",     "3", "You are a",           "r3"],
        ["PREFIX_LOOKUP", "4", "You are a helpful assistant"],
    ]
    assert solution(queries) == ["", "", "", "You are a"]


def test_prefix_lookup_excludes_expired():
    # Longer match is expired — should fall back to shorter live match
    queries = [
        ["CACHE_PUT",         "1", "sys",       "r-short"],
        ["CACHE_PUT_WITH_TTL","2", "sys prompt", "r-long", "5"],
        ["PREFIX_LOOKUP",     "8", "sys prompt today"],  # "sys prompt" expired at ts=7
    ]
    assert solution(queries) == ["", "", "sys"]


def test_prefix_lookup_increments_hit_count():
    queries = [
        ["CACHE_PUT",     "1", "prefix", "r"],
        ["PREFIX_LOOKUP", "2", "prefix extension"],
        ["HIT_COUNT",     "3", "prefix"],
    ]
    assert solution(queries) == ["", "prefix", "1"]


def test_prefix_lookup_updates_last_access_for_lru():
    # A(la=1) and B(la=2) at capacity=2. PREFIX_LOOKUP hits A → A.la=3.
    # Then add C → evict B (la=2, oldest).
    queries = [
        ["CACHE_PUT",    "1", "A-prefix",   "r"],
        ["CACHE_PUT",    "2", "B-other",    "r"],
        ["SET_CAPACITY", "3", "2"],
        ["PREFIX_LOOKUP","4", "A-prefix-extended"],  # hits A, A.la → 4
        ["CACHE_PUT",    "5", "C-new",      "r"],    # exceeds cap → evict LRU = B(la=2)
        ["CACHE_GET",    "6", "A-prefix"],            # still here
        ["CACHE_GET",    "7", "B-other"],             # evicted
        ["CACHE_GET",    "8", "C-new"],               # still here
    ]
    assert solution(queries) == ["", "", "0", "A-prefix", "", "r", "", "r"]


def test_prefix_lookup_no_match_no_hit_count_change():
    queries = [
        ["CACHE_PUT",     "1", "hello", "r"],
        ["PREFIX_LOOKUP", "2", "goodbye"],
        ["HIT_COUNT",     "3", "hello"],
    ]
    assert solution(queries) == ["", "", "0"]


def test_prefix_lookup_multiple_matches_same_length_impossible_but_alphabetical():
    # Two different strings of equal length can't both be prefixes of the same longer string,
    # but we test that the longer one wins (not the alphabetical first).
    queries = [
        ["CACHE_PUT",     "1", "ab",  "r1"],
        ["CACHE_PUT",     "2", "abc", "r2"],
        ["PREFIX_LOOKUP", "3", "abcdef"],
    ]
    # "abc" (3 chars) > "ab" (2 chars) → "abc" wins
    assert solution(queries) == ["", "", "abc"]


def test_invalidate_prefix_basic():
    queries = [
        ["CACHE_PUT",          "1", "abc",    "r1"],
        ["CACHE_PUT",          "2", "abcdef", "r2"],
        ["CACHE_PUT",          "3", "xyz",    "r3"],
        ["INVALIDATE_PREFIX",  "4", "abc"],
    ]
    assert solution(queries) == ["", "", "", "2"]


def test_invalidate_prefix_no_match():
    queries = [
        ["CACHE_PUT",         "1", "hello", "r"],
        ["INVALIDATE_PREFIX", "2", "world"],
    ]
    assert solution(queries) == ["", "0"]


def test_invalidate_prefix_deletes_expired_too():
    # Expired entries should ALSO be deleted by INVALIDATE_PREFIX
    queries = [
        ["CACHE_PUT_WITH_TTL","1", "abc-live",    "r", "100"],
        ["CACHE_PUT_WITH_TTL","2", "abc-expired", "r", "3"],   # expires at ts=5
        ["INVALIDATE_PREFIX", "6", "abc"],  # "abc-expired" is expired but still deleted
    ]
    assert solution(queries) == ["", "", "2"]


def test_invalidate_prefix_does_not_delete_non_matching():
    queries = [
        ["CACHE_PUT",         "1", "sys: you are",    "r1"],
        ["CACHE_PUT",         "2", "sys: be helpful", "r2"],
        ["CACHE_PUT",         "3", "user: hello",     "r3"],
        ["INVALIDATE_PREFIX", "4", "sys: "],
    ]
    # Only the two "sys: *" entries are deleted
    assert solution(queries) == ["", "", "", "2"]


def test_invalidate_prefix_then_get():
    queries = [
        ["CACHE_PUT",         "1", "hello world",  "r"],
        ["INVALIDATE_PREFIX", "2", "hello"],
        ["CACHE_GET",         "3", "hello world"],
    ]
    assert solution(queries) == ["", "1", ""]


def test_prefix_lookup_after_invalidate():
    queries = [
        ["CACHE_PUT",         "1", "sys",        "r1"],
        ["CACHE_PUT",         "2", "sys prompt", "r2"],
        ["INVALIDATE_PREFIX", "3", "sys"],
        ["PREFIX_LOOKUP",     "4", "sys prompt extended"],
    ]
    assert solution(queries) == ["", "", "2", ""]


def test_invalidate_prefix_exact_string_also_deleted():
    queries = [
        ["CACHE_PUT",         "1", "abc",    "r"],
        ["CACHE_PUT",         "2", "abcdef", "r"],
        ["INVALIDATE_PREFIX", "3", "abc"],   # "abc" itself starts with "abc"
        ["CACHE_GET",         "4", "abc"],
    ]
    assert solution(queries) == ["", "", "2", ""]


def test_worked_example_from_spec():
    queries = [
        ["CACHE_PUT",         "1",  "You are a helpful assistant.",           "sys-resp"],
        ["CACHE_PUT",         "2",  "You are a helpful assistant. User: hi",  "hi-resp"],
        ["CACHE_PUT",         "3",  "You are a helpful assistant. User: bye", "bye-resp"],
        ["CACHE_PUT",         "4",  "Tell me a joke",                         "joke-resp"],
        ["PREFIX_LOOKUP",     "5",  "You are a helpful assistant. User: hi, how are you?"],
        ["PREFIX_LOOKUP",     "6",  "You are a helpful assistant. User: hi"],
        ["PREFIX_LOOKUP",     "7",  "Completely different prompt"],
        ["HIT_COUNT",         "8",  "You are a helpful assistant. User: hi"],
        ["HIT_COUNT",         "9",  "You are a helpful assistant."],
        ["INVALIDATE_PREFIX", "10", "You are a helpful assistant"],
        ["CACHE_GET",         "11", "Tell me a joke"],
        ["CACHE_GET",         "12", "You are a helpful assistant."],
        ["PREFIX_LOOKUP",     "13", "You are a helpful assistant. User: hello"],
    ]
    assert solution(queries) == [
        "", "", "", "",
        "You are a helpful assistant. User: hi",
        "You are a helpful assistant. User: hi",
        "",
        "2", "0",
        "3",
        "joke-resp",
        "",
        "",
    ]


def test_prefix_lookup_empty_cache():
    queries = [["PREFIX_LOOKUP", "1", "anything"]]
    assert solution(queries) == [""]


def test_hit_count_incremented_by_prefix_lookup():
    # Two prefix lookups on same entry → hit count = 2
    queries = [
        ["CACHE_PUT",     "1", "sys",       "r"],
        ["PREFIX_LOOKUP", "2", "sys hello"],
        ["PREFIX_LOOKUP", "3", "sys world"],
        ["HIT_COUNT",     "4", "sys"],
    ]
    assert solution(queries) == ["", "sys", "sys", "2"]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 4 complete — congratulations!")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
