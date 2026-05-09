"""
Level 4 tests — run with: python test_level4.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_compress_basic():
    # alice uploads 400-byte file → compress → floor(400/2)=200. Return "200".
    queries = [
        ["USER_REGISTER",  "1", "alice", "1000"],
        ["USER_UPLOAD",    "2", "alice", "big.bin", "400"],   # rem=600
        ["COMPRESS_FILE",  "3", "alice", "big.bin"],          # 400→200, rem=800
    ]
    assert solution(queries) == ["true", "600", "200"]


def test_compress_odd_size_floor_division():
    # size=7, floor(7/2)=3
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "odd.bin", "7"],
        ["COMPRESS_FILE", "3", "alice", "odd.bin"],
    ]
    assert solution(queries) == ["true", "993", "3"]


def test_compress_size_one():
    # size=1, floor(1/2)=0
    queries = [
        ["USER_REGISTER", "1", "alice", "100"],
        ["USER_UPLOAD",   "2", "alice", "tiny.bin", "1"],
        ["COMPRESS_FILE", "3", "alice", "tiny.bin"],
    ]
    assert solution(queries) == ["true", "99", "0"]


def test_compress_frees_capacity():
    # alice cap=500, upload 400 (rem=100), compress 400→200 (rem=300), now can upload 250
    queries = [
        ["USER_REGISTER", "1", "alice", "500"],
        ["USER_UPLOAD",   "2", "alice", "big.bin",   "400"],   # rem=100
        ["USER_UPLOAD",   "3", "alice", "small.bin", "150"],   # exceeds: 400+150=550>500
        ["COMPRESS_FILE", "4", "alice", "big.bin"],            # 400→200, rem=300
        ["USER_UPLOAD",   "5", "alice", "small.bin", "150"],   # now fits: used=350, rem=150
    ]
    assert solution(queries) == ["true", "100", "", "200", "150"]


def test_compress_double_compress_rejected():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "file.bin", "400"],
        ["COMPRESS_FILE", "3", "alice", "file.bin"],   # ok → "200"
        ["COMPRESS_FILE", "4", "alice", "file.bin"],   # already compressed → ""
    ]
    assert solution(queries) == ["true", "600", "200", ""]


def test_compress_not_owned_returns_empty():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "1000"],
        ["USER_UPLOAD",   "3", "alice", "file.bin", "200"],
        ["COMPRESS_FILE", "4", "bob",   "file.bin"],   # not bob's
    ]
    assert solution(queries) == ["true", "true", "800", ""]


def test_compress_missing_file_returns_empty():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["COMPRESS_FILE", "2", "alice", "ghost.bin"],
    ]
    assert solution(queries) == ["true", ""]


def test_compress_unknown_user_returns_empty():
    queries = [
        ["FILE_UPLOAD",  "1", "file.bin", "400"],
        ["COMPRESS_FILE","2", "ghost",    "file.bin"],
    ]
    assert solution(queries) == ["true", ""]


def test_decompress_basic():
    # alice: upload 400 (rem=600), compress→200 (rem=800), decompress→400 (rem=600)
    queries = [
        ["USER_REGISTER",   "1", "alice", "1000"],
        ["USER_UPLOAD",     "2", "alice", "big.bin", "400"],  # rem=600
        ["COMPRESS_FILE",   "3", "alice", "big.bin"],         # rem=800, returns "200"
        ["DECOMPRESS_FILE", "4", "alice", "big.bin"],         # delta=200, rem=600
    ]
    assert solution(queries) == ["true", "600", "200", "600"]


def test_decompress_not_compressed_returns_empty():
    queries = [
        ["USER_REGISTER",   "1", "alice", "1000"],
        ["USER_UPLOAD",     "2", "alice", "file.bin", "200"],
        ["DECOMPRESS_FILE", "3", "alice", "file.bin"],   # not compressed
    ]
    assert solution(queries) == ["true", "800", ""]


def test_decompress_double_decompress_rejected():
    queries = [
        ["USER_REGISTER",   "1", "alice", "1000"],
        ["USER_UPLOAD",     "2", "alice", "f.bin", "400"],
        ["COMPRESS_FILE",   "3", "alice", "f.bin"],         # → 200
        ["DECOMPRESS_FILE", "4", "alice", "f.bin"],         # → 400, rem=600
        ["DECOMPRESS_FILE", "5", "alice", "f.bin"],         # not compressed → ""
    ]
    assert solution(queries) == ["true", "600", "200", "600", ""]


def test_decompress_exceeds_capacity_returns_empty():
    # alice cap=500, upload 400 (rem=100), compress→200 (rem=300).
    # Now add another 250-byte file (rem=50).
    # Decompress big.bin: delta=200, but rem=50 < 200 → fail.
    queries = [
        ["USER_REGISTER",   "1", "alice", "500"],
        ["USER_UPLOAD",     "2", "alice", "big.bin",   "400"],  # rem=100
        ["COMPRESS_FILE",   "3", "alice", "big.bin"],           # →200, rem=300
        ["USER_UPLOAD",     "4", "alice", "other.bin", "250"],  # rem=50
        ["DECOMPRESS_FILE", "5", "alice", "big.bin"],           # delta=200 > rem=50 → ""
    ]
    assert solution(queries) == ["true", "100", "200", "50", ""]


def test_decompress_exactly_fits():
    # cap=500, upload 400 (rem=100), compress→200 (rem=300), upload 100 (rem=200).
    # Decompress: delta=200, rem=200 → exactly fits → rem becomes 0.
    queries = [
        ["USER_REGISTER",   "1", "alice", "500"],
        ["USER_UPLOAD",     "2", "alice", "big.bin",  "400"],  # rem=100
        ["COMPRESS_FILE",   "3", "alice", "big.bin"],          # →200, rem=300
        ["USER_UPLOAD",     "4", "alice", "fill.bin", "100"],  # rem=200
        ["DECOMPRESS_FILE", "5", "alice", "big.bin"],          # delta=200=rem → rem=0
    ]
    assert solution(queries) == ["true", "100", "200", "200", "0"]


def test_merge_basic():
    # alice cap=1000, used=400, rem=600
    # bob   cap=600,  used=200, rem=400
    # merge → alice cap=1600, used=600, rem=1000
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "600"],
        ["USER_UPLOAD",   "3", "alice", "big.bin",   "400"],  # alice rem=600
        ["USER_UPLOAD",   "4", "bob",   "small.txt", "200"],  # bob rem=400
        ["USER_MERGE",    "5", "alice", "bob"],               # rem=1000
    ]
    assert solution(queries) == ["true", "true", "600", "400", "1000"]


def test_merge_transfers_file_ownership():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "600"],
        ["USER_UPLOAD",   "3", "bob",   "bob_file.txt", "100"],
        ["USER_MERGE",    "4", "alice", "bob"],
        ["USER_GET",      "5", "alice", "bob_file.txt"],   # alice now owns it
        ["USER_GET",      "6", "bob",   "bob_file.txt"],   # bob is gone
    ]
    # merge: alice cap=1600, used=100, rem=1500
    assert solution(queries) == ["true", "true", "500", "1500", "100", ""]


def test_merge_b_is_deleted_afterwards():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "600"],
        ["USER_MERGE",    "3", "alice", "bob"],
        ["USER_UPLOAD",   "4", "bob",   "new.txt", "50"],   # bob gone
        ["USER_REGISTER", "5", "bob",   "200"],             # re-registering bob is fine
        ["USER_UPLOAD",   "6", "bob",   "new.txt", "50"],   # bob exists again
    ]
    # merge: alice cap=1600, used=0, rem=1600
    assert solution(queries) == ["true", "true", "1600", "", "true", "150"]


def test_merge_global_namespace_prevents_same_name_upload():
    # Because the namespace is global, two users can never own a file with the
    # same name via USER_UPLOAD — so USER_MERGE name conflicts cannot arise
    # through normal uploads. This test verifies that invariant and confirms
    # a merge between users with distinct names succeeds correctly.
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "1000"],
        ["USER_UPLOAD",   "3", "alice", "conflict.txt", "100"],
        # bob tries the same name — must fail due to global namespace
        ["USER_UPLOAD",   "4", "bob",   "conflict.txt", "200"],
        # bob's upload failed so merge is clean
        ["USER_MERGE",    "5", "alice", "bob"],
    ]
    # alice: used=100, rem=900. bob: used=0, rem=1000.
    # merge: alice cap=2000, used=100, rem=1900.
    assert solution(queries) == ["true", "true", "900", "", "1900"]


def test_merge_same_user_returns_empty():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_MERGE",    "2", "alice", "alice"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_nonexistent_user_a_returns_empty():
    queries = [
        ["USER_REGISTER", "1", "bob", "600"],
        ["USER_MERGE",    "2", "ghost", "bob"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_nonexistent_user_b_returns_empty():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_MERGE",    "2", "alice", "ghost"],
    ]
    assert solution(queries) == ["true", ""]


def test_merge_preserves_compression_state():
    # bob has a compressed file; after merge it's still compressed under alice
    queries = [
        ["USER_REGISTER",   "1", "alice", "1000"],
        ["USER_REGISTER",   "2", "bob",   "600"],
        ["USER_UPLOAD",     "3", "bob",   "data.csv", "200"],  # bob rem=400
        ["COMPRESS_FILE",   "4", "bob",   "data.csv"],         # →100, bob rem=500
        ["USER_MERGE",      "5", "alice", "bob"],
        # alice cap=1600, used=100 (compressed size), rem=1500
        ["DECOMPRESS_FILE", "6", "alice", "data.csv"],         # delta=100, rem=1400
    ]
    assert solution(queries) == ["true", "true", "400", "100", "1500", "1400"]


def test_spec_full_worked_example():
    queries = [
        ["USER_REGISTER",   "1",  "alice",  "1000"],
        ["USER_REGISTER",   "2",  "bob",    "600"],
        ["USER_UPLOAD",     "3",  "alice",  "big.bin",    "400"],
        ["USER_UPLOAD",     "4",  "bob",    "small.txt",  "100"],
        ["USER_UPLOAD",     "5",  "bob",    "data.csv",   "200"],
        ["COMPRESS_FILE",   "6",  "alice",  "big.bin"],
        ["COMPRESS_FILE",   "7",  "alice",  "big.bin"],
        ["DECOMPRESS_FILE", "8",  "alice",  "big.bin"],
        ["DECOMPRESS_FILE", "9",  "alice",  "big.bin"],
        ["COMPRESS_FILE",   "10", "bob",    "data.csv"],
        ["USER_MERGE",      "11", "alice",  "bob"],
        ["USER_GET",        "12", "alice",  "small.txt"],
        ["USER_GET",        "13", "bob",    "small.txt"],
        ["DECOMPRESS_FILE", "14", "alice",  "data.csv"],
    ]
    assert solution(queries) == [
        "true", "true",
        "600", "500", "300",
        "200",   # compress big.bin: 400→200, alice rem=800
        "",      # double compress
        "600",   # decompress big.bin: 200→400, rem=600
        "",      # decompress again (not compressed)
        "100",   # compress data.csv: 200→100, bob rem=400
        "1000",  # merge: alice cap=1600, used=400+100+100=600, rem=1000
        "100",   # alice owns small.txt now
        "",      # bob gone
        "900",   # decompress data.csv: 100→200, delta=100, rem=1000-100=900
    ]


def test_compress_then_user_search_shows_compressed_size():
    # Compressed size is what FILE_SEARCH / USER_SEARCH should show.
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "doc.txt", "400"],
        ["COMPRESS_FILE", "3", "alice", "doc.txt"],   # → 200
        ["USER_SEARCH",   "4", "alice", "doc"],
    ]
    assert solution(queries) == ["true", "600", "200", "doc.txt(200)"]


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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 4 complete — you've built the full file system!")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
