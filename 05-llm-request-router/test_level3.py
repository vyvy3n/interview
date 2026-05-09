"""
Level 3 tests — run with: python test_level3.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_prefix_route_no_hit_falls_back_to_least_loaded():
    # Neither GPU has prefix; fallback = least-loaded (both at 0 → gpu-a alpha)
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["REGISTER_GPU",              "2", "gpu-b", "4"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-1", "pfx:sys", "100"],
    ]
    assert solution(queries) == ["true", "true", "gpu-a"]


def test_prefix_route_hit_beats_less_loaded():
    # gpu-b has prefix but is at 1 active; gpu-a has 0 active but no prefix.
    # gpu-b wins because it has the prefix and still has capacity.
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["REGISTER_GPU",              "2", "gpu-b", "4"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-1", "pfx:sys", "100"],  # gpu-a (fallback, tie alpha)
        # Now gpu-a has prefix pfx:sys at 1 active; gpu-b at 0, no prefix
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-2", "pfx:sys", "100"],  # gpu-a has prefix & cap
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "gpu-a"]


def test_prefix_route_hit_gpu_full_fallback():
    # Only one GPU has prefix but it's full; fallback to other GPU (no prefix but has capacity)
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "1"],
        ["REGISTER_GPU",              "2", "gpu-b", "2"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-1", "pfx:sys", "100"],  # gpu-a (fallback tie alpha, both 0)
        # gpu-a now 1/1 (full), has pfx:sys; gpu-b 0/2, no prefix
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-2", "pfx:sys", "100"],  # gpu-a has prefix but FULL → fallback → gpu-b
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "gpu-b"]


def test_get_cached_prefixes_mru_first():
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["ROUTE_REQUEST_WITH_PREFIX", "2", "req-1", "pfx:A", "100"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-2", "pfx:B", "100"],  # pfx:B now MRU, pfx:A LRU
        ["GET_CACHED_PREFIXES",       "4", "gpu-a"],
    ]
    assert solution(queries) == ["true", "gpu-a", "gpu-a", "pfx:B, pfx:A"]


def test_get_cached_prefixes_lru_update_on_hit():
    # pfx:A added first; pfx:B added second; then pfx:A is accessed again (hit) → pfx:A becomes MRU
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["ROUTE_REQUEST_WITH_PREFIX", "2", "req-1", "pfx:A", "100"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-2", "pfx:B", "100"],
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-3", "pfx:A", "100"],   # pfx:A hit → move to MRU
        ["GET_CACHED_PREFIXES",       "5", "gpu-a"],
    ]
    # After req-3: pfx:A is MRU, pfx:B is LRU
    assert solution(queries) == ["true", "gpu-a", "gpu-a", "gpu-a", "pfx:A, pfx:B"]


def test_get_cached_prefixes_empty_gpu():
    queries = [
        ["REGISTER_GPU",        "1", "gpu-a", "4"],
        ["GET_CACHED_PREFIXES", "2", "gpu-a"],
    ]
    assert solution(queries) == ["true", ""]


def test_get_cached_prefixes_unknown_gpu():
    queries = [
        ["GET_CACHED_PREFIXES", "1", "gpu-z"],
    ]
    assert solution(queries) == [""]


def test_lru_eviction_at_exactly_5_prefixes():
    # Fill cache to 5, then add a 6th → LRU (pfx:1) is evicted
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "10"],
        ["ROUTE_REQUEST_WITH_PREFIX", "2", "req-1", "pfx:1", "10"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-2", "pfx:2", "10"],
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-3", "pfx:3", "10"],
        ["ROUTE_REQUEST_WITH_PREFIX", "5", "req-4", "pfx:4", "10"],
        ["ROUTE_REQUEST_WITH_PREFIX", "6", "req-5", "pfx:5", "10"],
        # Cache is now [pfx:5, pfx:4, pfx:3, pfx:2, pfx:1] (MRU→LRU)
        ["GET_CACHED_PREFIXES",       "7", "gpu-a"],
        ["ROUTE_REQUEST_WITH_PREFIX", "8", "req-6", "pfx:6", "10"],
        # pfx:1 should be evicted; cache: [pfx:6, pfx:5, pfx:4, pfx:3, pfx:2]
        ["GET_CACHED_PREFIXES",       "9", "gpu-a"],
    ]
    assert solution(queries) == [
        "true",
        "gpu-a", "gpu-a", "gpu-a", "gpu-a", "gpu-a",
        "pfx:5, pfx:4, pfx:3, pfx:2, pfx:1",
        "gpu-a",
        "pfx:6, pfx:5, pfx:4, pfx:3, pfx:2",
    ]


def test_lru_eviction_lru_slot_is_least_recently_accessed():
    # Access pfx:1 after adding pfx:2 and pfx:3 → pfx:1 is MRU; pfx:2 is LRU
    # Then add pfx:4 and pfx:5 and pfx:6 → pfx:2 evicted (LRU after pfx:1 was refreshed)
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "10"],
        ["ROUTE_REQUEST_WITH_PREFIX", "2", "req-1", "pfx:1", "10"],  # cache: [pfx:1]
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-2", "pfx:2", "10"],  # cache: [pfx:2, pfx:1]
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-3", "pfx:3", "10"],  # cache: [pfx:3, pfx:2, pfx:1]
        ["ROUTE_REQUEST_WITH_PREFIX", "5", "req-4", "pfx:1", "10"],  # hit pfx:1 → cache: [pfx:1, pfx:3, pfx:2]
        ["ROUTE_REQUEST_WITH_PREFIX", "6", "req-5", "pfx:4", "10"],  # cache: [pfx:4, pfx:1, pfx:3, pfx:2]
        ["ROUTE_REQUEST_WITH_PREFIX", "7", "req-6", "pfx:5", "10"],  # cache: [pfx:5, pfx:4, pfx:1, pfx:3, pfx:2] (full)
        ["ROUTE_REQUEST_WITH_PREFIX", "8", "req-7", "pfx:6", "10"],  # evict LRU=pfx:2 → [pfx:6, pfx:5, pfx:4, pfx:1, pfx:3]
        ["GET_CACHED_PREFIXES",       "9", "gpu-a"],
    ]
    assert solution(queries) == [
        "true",
        "gpu-a", "gpu-a", "gpu-a", "gpu-a", "gpu-a", "gpu-a", "gpu-a",
        "pfx:6, pfx:5, pfx:4, pfx:1, pfx:3",
    ]


def test_plain_route_request_does_not_touch_cache():
    # ROUTE_REQUEST (no prefix) must not modify the cache
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["ROUTE_REQUEST_WITH_PREFIX", "2", "req-1", "pfx:A", "100"],
        ["ROUTE_REQUEST",             "3", "req-2", "200"],           # plain route, no cache change
        ["GET_CACHED_PREFIXES",       "4", "gpu-a"],
    ]
    # Cache should still only have pfx:A
    assert solution(queries) == ["true", "gpu-a", "gpu-a", "pfx:A"]


def test_prefix_aware_multi_gpu_affinity():
    # gpu-a gets pfx:chat; gpu-b gets pfx:code; then same prefixes should stick
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["REGISTER_GPU",              "2", "gpu-b", "4"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-1", "pfx:chat", "100"],  # fallback, gpu-a (alpha)
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-2", "pfx:code", "100"],  # fallback, gpu-b (gpu-a at 1, gpu-b at 0)
        ["ROUTE_REQUEST_WITH_PREFIX", "5", "req-3", "pfx:chat", "100"],  # gpu-a has prefix → gpu-a
        ["ROUTE_REQUEST_WITH_PREFIX", "6", "req-4", "pfx:code", "100"],  # gpu-b has prefix → gpu-b
        ["GET_CACHED_PREFIXES",       "7", "gpu-a"],
        ["GET_CACHED_PREFIXES",       "8", "gpu-b"],
    ]
    assert solution(queries) == [
        "true", "true",
        "gpu-a", "gpu-b", "gpu-a", "gpu-b",
        "pfx:chat",
        "pfx:code",
    ]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_GPU",              "1",  "gpu-a", "3"],
        ["REGISTER_GPU",              "2",  "gpu-b", "3"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3",  "req-1", "sys:assistant", "512"],
        ["ROUTE_REQUEST_WITH_PREFIX", "4",  "req-2", "sys:assistant", "256"],
        ["ROUTE_REQUEST_WITH_PREFIX", "5",  "req-3", "sys:user",      "128"],
        ["GET_CACHED_PREFIXES",       "6",  "gpu-a"],
        ["GET_CACHED_PREFIXES",       "7",  "gpu-b"],
        ["ROUTE_REQUEST_WITH_PREFIX", "8",  "req-4", "sys:assistant", "64"],
        ["GET_CACHED_PREFIXES",       "9",  "gpu-a"],
        ["COMPLETE_REQUEST",          "10", "req-2"],
        ["ROUTE_REQUEST_WITH_PREFIX", "11", "req-5", "sys:assistant", "64"],
        ["GET_CACHED_PREFIXES",       "12", "gpu-b"],
    ]
    assert solution(queries) == [
        "true", "true",
        "gpu-a", "gpu-a", "gpu-b",
        "sys:assistant", "sys:user",
        "gpu-a",
        "sys:assistant",
        "true",
        "gpu-a",
        "sys:user",
    ]


def test_no_capacity_with_prefix_returns_empty():
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "1"],
        ["ROUTE_REQUEST_WITH_PREFIX", "2", "req-1", "pfx:A", "100"],  # fills gpu-a
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-2", "pfx:A", "100"],  # gpu-a full → ""
    ]
    assert solution(queries) == ["true", "gpu-a", ""]


def test_prefix_hit_across_two_gpus_pick_least_loaded():
    # Both gpus have the prefix; pick least loaded among them
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["REGISTER_GPU",              "2", "gpu-b", "4"],
        # Seed both caches with pfx:shared via fallback routing
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-1", "pfx:shared", "10"],  # gpu-a (fallback, alpha)
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-2", "pfx:other",  "10"],  # gpu-b (fallback, fewer active)
        ["COMPLETE_REQUEST",          "5", "req-1"],                       # gpu-a back to 0
        ["ROUTE_REQUEST_WITH_PREFIX", "6", "req-3", "pfx:shared", "10"],  # gpu-a has prefix, 0 active; gpu-b has no prefix
        # Now seed gpu-b with pfx:shared
        ["ROUTE_REQUEST_WITH_PREFIX", "7", "req-4", "pfx:shared", "10"],  # gpu-a has prefix (1 active); gpu-b no pfx
        ["ROUTE_REQUEST_WITH_PREFIX", "8", "req-5", "pfx:shared", "10"],  # gpu-a (2 active); gpu-b still no pfx
        # Add pfx:shared to gpu-b explicitly
        ["ROUTE_REQUEST_WITH_PREFIX", "9", "req-6", "pfx:shared", "10"],  # gpu-a (3 active); gpu-b no pfx
    ]
    # gpu-a gets req-1(fallback), req-3(hit), req-4(hit), req-5(hit), req-6(hit)
    # gpu-b gets req-2(fallback pfx:other)
    assert solution(queries) == [
        "true", "true",
        "gpu-a", "gpu-b",
        "true",
        "gpu-a", "gpu-a", "gpu-a", "gpu-a",
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
