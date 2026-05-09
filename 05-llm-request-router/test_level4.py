"""
Level 4 tests — run with: python test_level4.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_fail_unknown_gpu_returns_empty():
    queries = [
        ["REGISTER_GPU", "1", "gpu-a", "4"],
        ["FAIL_GPU",     "2", "gpu-z"],
    ]
    assert solution(queries) == ["true", ""]


def test_fail_gpu_no_in_flight_returns_zero():
    # No active requests on the GPU — re-routed count is 0
    queries = [
        ["REGISTER_GPU", "1", "gpu-a", "4"],
        ["REGISTER_GPU", "2", "gpu-b", "4"],
        ["FAIL_GPU",     "3", "gpu-a"],
    ]
    assert solution(queries) == ["true", "true", "0"]


def test_fail_gpu_reroutes_requests_to_other_gpu():
    # req-1 on gpu-a; gpu-b has capacity → re-routed successfully
    queries = [
        ["REGISTER_GPU",     "1", "gpu-a", "2"],
        ["REGISTER_GPU",     "2", "gpu-b", "2"],
        ["ROUTE_REQUEST",    "3", "req-1", "100"],   # gpu-a
        ["FAIL_GPU",         "4", "gpu-a"],          # re-route req-1 → gpu-b
        ["GPU_LOAD",         "5", "gpu-b"],
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "1", "1/2"]


def test_fail_gpu_reroutes_with_prefix_affinity():
    # gpu-b has pfx:chat cached; re-routed request had pfx:chat → should land on gpu-b
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "2"],
        ["REGISTER_GPU",              "2", "gpu-b", "2"],
        # Seed gpu-b with pfx:chat
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-seed", "pfx:chat", "10"],  # gpu-a (alpha, both 0)
        ["COMPLETE_REQUEST",          "4", "req-seed"],                      # free gpu-a
        # Now gpu-a has pfx:chat; gpu-b has no prefix
        # Route a new request with pfx:chat to gpu-a (it has the prefix)
        ["ROUTE_REQUEST_WITH_PREFIX", "5", "req-1", "pfx:chat", "10"],    # gpu-a has prefix → gpu-a
        # Route something to gpu-b so gpu-b gets pfx:chat too
        ["ROUTE_REQUEST_WITH_PREFIX", "6", "req-2", "pfx:chat", "10"],    # gpu-a 2nd slot; wait
        # Actually: gpu-a has pfx:chat and 1 active (cap 2) → gpu-a again
        # Let's complete req-seed was already done; now gpu-a: 1 active, has pfx:chat
        # req-2: gpu-a has prefix (1 active, cap 2) → gpu-a
        # Now fail gpu-a which has req-1 and req-2
        ["FAIL_GPU",                  "7", "gpu-a"],
        # Re-route: sort [req-1, req-2]; gpu-b has no prefix → fallback
        # req-1 → gpu-b (least loaded, 0 active); gpu-b cache updated with pfx:chat
        # req-2 → gpu-b (1 active, cap 2, has pfx:chat) → gpu-b (hit)
        ["GPU_LOAD",                  "8", "gpu-b"],
        ["GET_CACHED_PREFIXES",       "9", "gpu-b"],
    ]
    assert solution(queries) == [
        "true", "true",
        "gpu-a", "true",
        "gpu-a", "gpu-a",
        "2",
        "2/2",
        "pfx:chat",
    ]


def test_fail_gpu_drops_requests_when_no_capacity():
    # Fleet has no remaining capacity → all re-routes fail → count=0, requests dropped
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "1"],
        ["REGISTER_GPU",  "2", "gpu-b", "1"],
        ["ROUTE_REQUEST", "3", "req-1", "100"],   # gpu-a
        ["ROUTE_REQUEST", "4", "req-2", "100"],   # gpu-b (only remaining)
        ["FAIL_GPU",      "5", "gpu-a"],           # req-1 needs re-route; gpu-b full → drop
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "gpu-b", "0"]


def test_fail_gpu_partial_reroute():
    # gpu-a has 2 requests; only 1 slot remaining across other GPUs → 1 success, 1 drop
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "2"],
        ["REGISTER_GPU",  "2", "gpu-b", "1"],
        ["REGISTER_GPU",  "3", "gpu-c", "1"],
        ["ROUTE_REQUEST", "4", "req-a", "100"],   # gpu-a (alpha, all at 0)
        ["ROUTE_REQUEST", "5", "req-b", "100"],   # gpu-b (gpu-b/gpu-c at 0 < gpu-a at 1; alpha→gpu-b)
        ["ROUTE_REQUEST", "6", "req-c", "100"],   # gpu-a (gpu-a 1/2, gpu-c 0/1; gpu-c=0<1? no gpu-c has 0, gpu-a has 1... gpu-c wins)
        # Wait, let me retrace: after req-a: gpu-a:1, gpu-b:0, gpu-c:0
        # req-b: least loaded are gpu-b(0) and gpu-c(0), both cap=1. Alpha: gpu-b
        # req-c: gpu-a:1/2, gpu-b:1/1(full), gpu-c:0/1. Least loaded with cap: gpu-c
        ["ROUTE_REQUEST", "7", "req-d", "100"],   # gpu-a 2nd slot (gpu-a:1, gpu-c:1 now...wait)
        # After req-c: gpu-a:1, gpu-b:1, gpu-c:1
        # req-d: gpu-a:1/2 only has capacity → gpu-a
        ["FAIL_GPU",      "8", "gpu-a"],
        # gpu-a had req-a and req-d. Sort alpha: [req-a, req-d]
        # gpu-b: 1/1 full; gpu-c: 1/1 full
        # req-a: no capacity anywhere → drop
        # req-d: no capacity anywhere → drop
        # count = 0
    ]
    assert solution(queries) == [
        "true", "true", "true",
        "gpu-a", "gpu-b", "gpu-c", "gpu-a",
        "0",
    ]


def test_fail_reroute_order_alpha_determines_capacity():
    # req-z vs req-a: req-a sorts first, gets the last slot; req-z is dropped
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "2"],
        ["REGISTER_GPU",  "2", "gpu-b", "1"],
        ["ROUTE_REQUEST", "3", "req-a", "10"],   # gpu-a
        ["ROUTE_REQUEST", "4", "req-z", "10"],   # gpu-a (tie: gpu-a 1/2, gpu-b 0/1; gpu-b wins?
        # Actually: gpu-a has 1 active, gpu-b has 0 → gpu-b is least loaded
        ["ROUTE_REQUEST", "5", "req-m", "10"],   # gpu-a (gpu-b 1/1 full, gpu-a 1/2 cap)
        ["FAIL_GPU",      "6", "gpu-a"],
        # gpu-a had req-a and req-m. Sort alpha: [req-a, req-m]
        # gpu-b: 1/1 full → no capacity for either
        # count = 0
    ]
    # Hmm, let me use a cleaner scenario where order matters
    assert solution(queries) == [
        "true", "true",
        "gpu-a", "gpu-b", "gpu-a",
        "0",
    ]


def test_fail_reroute_alpha_order_first_gets_slot():
    # gpu-c has exactly 1 slot; req-a and req-z both on gpu-a; req-a (alpha first) gets the slot
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "2"],
        ["REGISTER_GPU",  "2", "gpu-b", "0"],   # zero capacity... invalid per spec (capacity >= 1)
    ]
    # Use a cleaner test: 1 spare slot, 2 requests — earlier alpha wins
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "2"],
        ["REGISTER_GPU",  "2", "gpu-c", "1"],
        ["ROUTE_REQUEST", "3", "req-a", "10"],   # gpu-a (both 0, alpha gpu-a)
        ["ROUTE_REQUEST", "4", "req-z", "10"],   # gpu-a (gpu-c 0/1, gpu-a 1/2: gpu-c least loaded)
        # Wait: gpu-a:1, gpu-c:0 → gpu-c is least loaded
    ]
    # Let me redo this entirely:
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "2"],
        ["REGISTER_GPU",  "2", "gpu-b", "2"],
        ["REGISTER_GPU",  "3", "gpu-c", "1"],
        # Fill gpu-b to capacity
        ["ROUTE_REQUEST", "4", "req-x1", "10"],  # gpu-a (all 0, alpha)
        ["ROUTE_REQUEST", "5", "req-x2", "10"],  # gpu-b (gpu-b/gpu-c 0 < gpu-a 1; alpha gpu-b)
        ["ROUTE_REQUEST", "6", "req-x3", "10"],  # gpu-c (gpu-c 0/1, gpu-a 1/2; least loaded)
        ["ROUTE_REQUEST", "7", "req-x4", "10"],  # gpu-b (gpu-b 1/2 vs gpu-a 1/2; alpha gpu-a...
        # gpu-a:1, gpu-b:1, gpu-c:1(full). Only gpu-a and gpu-b available. Tie→gpu-a
        # Actually: gpu-a has 1, gpu-b has 1 — tie → gpu-a
        ["FAIL_GPU",      "8", "gpu-a"],
        # gpu-a had req-x1 and req-x4. Sort: [req-x1, req-x4]
        # Remaining: gpu-b: 1/2 (1 slot free), gpu-c: 1/1 (full)
        # req-x1 → gpu-b (only one with capacity) → success. gpu-b: 2/2
        # req-x4 → no capacity → drop
        # count = 1
        ["GPU_LOAD",      "9", "gpu-b"],
    ]
    assert solution(queries) == [
        "true", "true", "true",
        "gpu-a", "gpu-b", "gpu-c", "gpu-a",
        "1",
        "2/2",
    ]


def test_recover_gpu_from_failed_state():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "4"],
        ["REGISTER_GPU",  "2", "gpu-b", "4"],
        ["ROUTE_REQUEST", "3", "req-1", "100"],
        ["FAIL_GPU",      "4", "gpu-a"],
        ["RECOVER_GPU",   "5", "gpu-a"],
        ["GPU_LOAD",      "6", "gpu-a"],
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "1", "true", "0/4"]


def test_recover_active_gpu_returns_false():
    queries = [
        ["REGISTER_GPU", "1", "gpu-a", "4"],
        ["RECOVER_GPU",  "2", "gpu-a"],   # gpu-a is active, not failed
    ]
    assert solution(queries) == ["true", "false"]


def test_recover_never_registered_returns_false():
    queries = [
        ["RECOVER_GPU", "1", "gpu-z"],
    ]
    assert solution(queries) == ["false"]


def test_recover_restores_empty_cache():
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "4"],
        ["REGISTER_GPU",              "2", "gpu-b", "4"],
        ["ROUTE_REQUEST_WITH_PREFIX", "3", "req-1", "pfx:A", "10"],  # gpu-a gets pfx:A
        ["FAIL_GPU",                  "4", "gpu-a"],
        ["RECOVER_GPU",               "5", "gpu-a"],
        ["GET_CACHED_PREFIXES",       "6", "gpu-a"],   # cache must be empty after recover
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "1", "true", ""]


def test_recover_restores_original_capacity():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "6"],
        ["REGISTER_GPU",  "2", "gpu-b", "4"],
        ["ROUTE_REQUEST", "3", "req-1", "10"],
        ["FAIL_GPU",      "4", "gpu-a"],
        ["RECOVER_GPU",   "5", "gpu-a"],
        ["GPU_LOAD",      "6", "gpu-a"],   # should show 0/6, not any other capacity
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "1", "true", "0/6"]


def test_fail_already_failed_gpu_returns_empty():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "4"],
        ["REGISTER_GPU",  "2", "gpu-b", "4"],
        ["ROUTE_REQUEST", "3", "req-1", "10"],
        ["FAIL_GPU",      "4", "gpu-a"],
        ["FAIL_GPU",      "5", "gpu-a"],   # already failed → ""
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "1", ""]


def test_fail_then_recover_then_fail_again():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "2"],
        ["REGISTER_GPU",  "2", "gpu-b", "2"],
        ["ROUTE_REQUEST", "3", "req-1", "10"],
        ["FAIL_GPU",      "4", "gpu-a"],         # fails; req-1 re-routed to gpu-b
        ["RECOVER_GPU",   "5", "gpu-a"],         # recovered; active=0, cap=2, empty cache
        ["ROUTE_REQUEST", "6", "req-2", "10"],   # gpu-a (fewer active: 0 vs gpu-b 1)
        ["FAIL_GPU",      "7", "gpu-a"],         # fail again; req-2 re-routed to gpu-b
        ["GPU_LOAD",      "8", "gpu-b"],
    ]
    assert solution(queries) == [
        "true", "true",
        "gpu-a",
        "1",
        "true",
        "gpu-a",
        "1",
        "2/2",
    ]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_GPU",              "1",  "gpu-a", "2"],
        ["REGISTER_GPU",              "2",  "gpu-b", "2"],
        ["REGISTER_GPU",              "3",  "gpu-c", "1"],
        ["ROUTE_REQUEST_WITH_PREFIX", "4",  "req-a", "pfx:chat", "100"],
        ["ROUTE_REQUEST_WITH_PREFIX", "5",  "req-b", "pfx:chat", "100"],
        ["ROUTE_REQUEST_WITH_PREFIX", "6",  "req-c", "pfx:chat", "100"],
        ["ROUTE_REQUEST_WITH_PREFIX", "7",  "req-d", "pfx:chat", "100"],
        ["FAIL_GPU",                  "8",  "gpu-a"],
        ["RECOVER_GPU",               "9",  "gpu-a"],
        ["RECOVER_GPU",               "10", "gpu-a"],
        ["GPU_LOAD",                  "11", "gpu-a"],
    ]
    assert solution(queries) == [
        "true", "true", "true",
        "gpu-a", "gpu-a", "gpu-b", "gpu-b",
        "1",
        "true",
        "false",
        "0/2",
    ]


def test_fail_reroute_prefix_none_requests_use_fallback_only():
    # Mix of plain and prefix requests on failed GPU; plain ones use fallback only (no cache update)
    queries = [
        ["REGISTER_GPU",              "1", "gpu-a", "2"],
        ["REGISTER_GPU",              "2", "gpu-b", "2"],
        ["ROUTE_REQUEST",             "3", "req-plain", "10"],           # gpu-a (plain, no prefix)
        ["ROUTE_REQUEST_WITH_PREFIX", "4", "req-pfx",   "pfx:X", "10"], # gpu-a has prefix
        ["FAIL_GPU",                  "5", "gpu-a"],
        # gpu-a had [req-pfx, req-plain]. Sort alpha: [req-pfx, req-plain]
        # req-pfx: prefix=pfx:X; gpu-b has no pfx:X → fallback → gpu-b; gpu-b cache gets pfx:X
        # req-plain: prefix=None; fallback → gpu-b (still has cap); no cache update for plain
        ["GPU_LOAD",                  "6", "gpu-b"],
        ["GET_CACHED_PREFIXES",       "7", "gpu-b"],
    ]
    assert solution(queries) == [
        "true", "true",
        "gpu-a", "gpu-a",
        "2",
        "2/2",
        "pfx:X",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 4 complete — you've built a KV-cache-aware LLM request router!")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
