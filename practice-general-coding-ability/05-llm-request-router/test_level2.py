"""
Level 2 tests — run with: python test_level2.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_gpu_load_basic():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "4"],
        ["ROUTE_REQUEST", "2", "req-1", "100"],
        ["ROUTE_REQUEST", "3", "req-2", "100"],
        ["GPU_LOAD",      "4", "gpu-a"],
    ]
    assert solution(queries) == ["true", "gpu-a", "gpu-a", "2/4"]


def test_gpu_load_idle_gpu():
    queries = [
        ["REGISTER_GPU", "1", "gpu-a", "8"],
        ["GPU_LOAD",     "2", "gpu-a"],
    ]
    assert solution(queries) == ["true", "0/8"]


def test_gpu_load_unknown_returns_empty():
    queries = [
        ["REGISTER_GPU", "1", "gpu-a", "4"],
        ["GPU_LOAD",     "2", "gpu-z"],
    ]
    assert solution(queries) == ["true", ""]


def test_gpu_load_reflects_completion():
    queries = [
        ["REGISTER_GPU",     "1", "gpu-a", "4"],
        ["ROUTE_REQUEST",    "2", "req-1", "100"],
        ["ROUTE_REQUEST",    "3", "req-2", "100"],
        ["GPU_LOAD",         "4", "gpu-a"],
        ["COMPLETE_REQUEST", "5", "req-1"],
        ["GPU_LOAD",         "6", "gpu-a"],
    ]
    assert solution(queries) == ["true", "gpu-a", "gpu-a", "2/4", "true", "1/4"]


def test_top_busiest_no_gpus_returns_empty():
    queries = [["TOP_BUSIEST", "1", "3"]]
    assert solution(queries) == [""]


def test_top_busiest_basic():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "4"],
        ["REGISTER_GPU",  "2", "gpu-b", "4"],
        ["REGISTER_GPU",  "3", "gpu-c", "4"],
        ["ROUTE_REQUEST", "4", "req-1", "100"],   # gpu-a
        ["ROUTE_REQUEST", "5", "req-2", "100"],   # gpu-b
        ["ROUTE_REQUEST", "6", "req-3", "100"],   # gpu-c
        ["ROUTE_REQUEST", "7", "req-4", "100"],   # gpu-a (tie broken alpha, gpu-a)
        ["TOP_BUSIEST",   "8", "2"],
    ]
    # gpu-a:2, gpu-b:1, gpu-c:1 → top 2 = gpu-a, then gpu-b (tie at 1, alpha)
    assert solution(queries) == ["true", "true", "true", "gpu-a", "gpu-b", "gpu-c", "gpu-a", "gpu-a(2/4), gpu-b(1/4)"]


def test_top_busiest_includes_idle_gpus():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "4"],
        ["REGISTER_GPU",  "2", "gpu-b", "4"],
        ["ROUTE_REQUEST", "3", "req-1", "100"],
        ["TOP_BUSIEST",   "4", "5"],   # k > num GPUs; include idle
    ]
    # gpu-a:1, gpu-b:0
    assert solution(queries) == ["true", "true", "gpu-a", "gpu-a(1/4), gpu-b(0/4)"]


def test_top_busiest_k_greater_than_gpu_count():
    queries = [
        ["REGISTER_GPU", "1", "gpu-x", "2"],
        ["TOP_BUSIEST",  "2", "10"],
    ]
    assert solution(queries) == ["true", "gpu-x(0/2)"]


def test_top_busiest_tie_broken_alphabetically():
    queries = [
        ["REGISTER_GPU", "1", "gpu-c", "2"],
        ["REGISTER_GPU", "2", "gpu-a", "2"],
        ["REGISTER_GPU", "3", "gpu-b", "2"],
        ["TOP_BUSIEST",  "4", "3"],   # all at 0, alpha order
    ]
    assert solution(queries) == ["true", "true", "true", "gpu-a(0/2), gpu-b(0/2), gpu-c(0/2)"]


def test_top_busiest_k_equals_one():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "4"],
        ["REGISTER_GPU",  "2", "gpu-b", "4"],
        ["ROUTE_REQUEST", "3", "req-1", "100"],
        ["ROUTE_REQUEST", "4", "req-2", "100"],
        ["ROUTE_REQUEST", "5", "req-3", "100"],   # gpu-a:2 (0→gpu-a, 1→gpu-b at 1, 2→gpu-a tie)
        ["TOP_BUSIEST",   "6", "1"],
    ]
    # After routing: req-1→gpu-a(1/4), req-2→gpu-b(1/4), req-3→gpu-a(2/4)
    assert solution(queries) == ["true", "true", "gpu-a", "gpu-b", "gpu-a", "gpu-a(2/4)"]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_GPU",     "1",  "gpu-a", "4"],
        ["REGISTER_GPU",     "2",  "gpu-b", "4"],
        ["REGISTER_GPU",     "3",  "gpu-c", "4"],
        ["ROUTE_REQUEST",    "4",  "req-1", "100"],
        ["ROUTE_REQUEST",    "5",  "req-2", "100"],
        ["ROUTE_REQUEST",    "6",  "req-3", "100"],
        ["ROUTE_REQUEST",    "7",  "req-4", "100"],
        ["GPU_LOAD",         "8",  "gpu-a"],
        ["GPU_LOAD",         "9",  "gpu-z"],
        ["TOP_BUSIEST",      "10", "2"],
        ["COMPLETE_REQUEST", "11", "req-1"],
        ["TOP_BUSIEST",      "12", "5"],
        ["TOP_BUSIEST",      "13", "1"],
    ]
    assert solution(queries) == [
        "true", "true", "true",
        "gpu-a", "gpu-b", "gpu-c", "gpu-a",
        "2/4", "",
        "gpu-a(2/4), gpu-b(1/4)",
        "true",
        "gpu-a(1/4), gpu-b(1/4), gpu-c(1/4)",
        "gpu-a(1/4)",
    ]


def test_gpu_load_full_capacity():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "2"],
        ["ROUTE_REQUEST", "2", "req-1", "10"],
        ["ROUTE_REQUEST", "3", "req-2", "10"],
        ["GPU_LOAD",      "4", "gpu-a"],
    ]
    assert solution(queries) == ["true", "gpu-a", "gpu-a", "2/2"]


def test_top_busiest_after_completions():
    queries = [
        ["REGISTER_GPU",     "1", "gpu-a", "4"],
        ["REGISTER_GPU",     "2", "gpu-b", "4"],
        ["ROUTE_REQUEST",    "3", "req-1", "10"],
        ["ROUTE_REQUEST",    "4", "req-2", "10"],
        ["ROUTE_REQUEST",    "5", "req-3", "10"],
        ["COMPLETE_REQUEST", "6", "req-1"],
        ["COMPLETE_REQUEST", "7", "req-2"],
        ["TOP_BUSIEST",      "8", "2"],
    ]
    # req-1→gpu-a, req-2→gpu-b, req-3→gpu-a; then complete req-1 (gpu-a:1) and req-2 (gpu-b:0)
    # After: gpu-a:1, gpu-b:0 → top 2: gpu-a(1/4), gpu-b(0/4)
    assert solution(queries) == ["true", "true", "gpu-a", "gpu-b", "gpu-a", "true", "true", "gpu-a(1/4), gpu-b(0/4)"]


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
