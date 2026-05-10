"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_register_single_gpu():
    queries = [["REGISTER_GPU", "1", "gpu-a", "4"]]
    assert solution(queries) == ["true"]


def test_register_duplicate_returns_false():
    queries = [
        ["REGISTER_GPU", "1", "gpu-a", "4"],
        ["REGISTER_GPU", "2", "gpu-a", "8"],   # duplicate
    ]
    assert solution(queries) == ["true", "false"]


def test_register_multiple_distinct_gpus():
    queries = [
        ["REGISTER_GPU", "1", "gpu-a", "4"],
        ["REGISTER_GPU", "2", "gpu-b", "2"],
        ["REGISTER_GPU", "3", "gpu-c", "1"],
    ]
    assert solution(queries) == ["true", "true", "true"]


def test_route_no_gpus_returns_empty():
    queries = [["ROUTE_REQUEST", "1", "req-1", "512"]]
    assert solution(queries) == [""]


def test_route_to_only_gpu():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "3"],
        ["ROUTE_REQUEST", "2", "req-1", "100"],
    ]
    assert solution(queries) == ["true", "gpu-a"]


def test_route_tie_broken_alphabetically():
    # Both GPUs at 0 active — gpu-a comes before gpu-b alphabetically
    queries = [
        ["REGISTER_GPU",  "1", "gpu-b", "2"],
        ["REGISTER_GPU",  "2", "gpu-a", "2"],
        ["ROUTE_REQUEST", "3", "req-1", "100"],
    ]
    assert solution(queries) == ["true", "true", "gpu-a"]


def test_route_least_loaded_wins():
    # gpu-a gets req-1 (tie→alpha); gpu-b has 0 active; req-2 → gpu-b (fewer active)
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "4"],
        ["REGISTER_GPU",  "2", "gpu-b", "4"],
        ["ROUTE_REQUEST", "3", "req-1", "100"],   # both at 0 → gpu-a
        ["ROUTE_REQUEST", "4", "req-2", "100"],   # gpu-a:1, gpu-b:0 → gpu-b
        ["ROUTE_REQUEST", "5", "req-3", "100"],   # gpu-a:1, gpu-b:1 → gpu-a (tie, alpha)
    ]
    assert solution(queries) == ["true", "true", "gpu-a", "gpu-b", "gpu-a"]


def test_route_returns_empty_when_all_full():
    queries = [
        ["REGISTER_GPU",  "1", "gpu-a", "1"],
        ["ROUTE_REQUEST", "2", "req-1", "100"],   # fills gpu-a
        ["ROUTE_REQUEST", "3", "req-2", "100"],   # gpu-a full → ""
    ]
    assert solution(queries) == ["true", "gpu-a", ""]


def test_complete_request_returns_true():
    queries = [
        ["REGISTER_GPU",     "1", "gpu-a", "2"],
        ["ROUTE_REQUEST",    "2", "req-1", "100"],
        ["COMPLETE_REQUEST", "3", "req-1"],
    ]
    assert solution(queries) == ["true", "gpu-a", "true"]


def test_complete_unknown_request_returns_false():
    queries = [
        ["REGISTER_GPU",     "1", "gpu-a", "2"],
        ["COMPLETE_REQUEST", "2", "req-ghost"],
    ]
    assert solution(queries) == ["true", "false"]


def test_complete_frees_slot_for_new_route():
    queries = [
        ["REGISTER_GPU",     "1", "gpu-a", "1"],
        ["ROUTE_REQUEST",    "2", "req-1", "100"],   # fills gpu-a
        ["ROUTE_REQUEST",    "3", "req-2", "100"],   # full → ""
        ["COMPLETE_REQUEST", "4", "req-1"],          # frees slot
        ["ROUTE_REQUEST",    "5", "req-2", "100"],   # now has room
    ]
    assert solution(queries) == ["true", "gpu-a", "", "true", "gpu-a"]


def test_worked_example_from_spec():
    queries = [
        ["REGISTER_GPU",     "1",  "gpu-a", "2"],
        ["REGISTER_GPU",     "2",  "gpu-b", "1"],
        ["REGISTER_GPU",     "3",  "gpu-a", "3"],   # duplicate
        ["ROUTE_REQUEST",    "4",  "req-1", "512"],
        ["ROUTE_REQUEST",    "5",  "req-2", "256"],
        ["ROUTE_REQUEST",    "6",  "req-3", "128"],
        ["ROUTE_REQUEST",    "7",  "req-4", "64"],
        ["COMPLETE_REQUEST", "8",  "req-1"],
        ["ROUTE_REQUEST",    "9",  "req-5", "100"],
        ["COMPLETE_REQUEST", "10", "req-99"],
    ]
    assert solution(queries) == [
        "true", "true", "false",
        "gpu-a", "gpu-b", "gpu-a", "",
        "true", "gpu-a", "false",
    ]


def test_capacity_one_multi_gpu():
    # Three GPUs each with cap=1; verify round-robin in alpha order as load spreads
    queries = [
        ["REGISTER_GPU",  "1", "gpu-c", "1"],
        ["REGISTER_GPU",  "2", "gpu-a", "1"],
        ["REGISTER_GPU",  "3", "gpu-b", "1"],
        ["ROUTE_REQUEST", "4", "req-1", "10"],   # gpu-a (alpha, all at 0)
        ["ROUTE_REQUEST", "5", "req-2", "10"],   # gpu-b (gpu-a full, gpu-b at 0 < gpu-c)
        ["ROUTE_REQUEST", "6", "req-3", "10"],   # gpu-c (only one left)
        ["ROUTE_REQUEST", "7", "req-4", "10"],   # all full → ""
    ]
    assert solution(queries) == ["true", "true", "true", "gpu-a", "gpu-b", "gpu-c", ""]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 1 complete — commit and request Level 2.")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
