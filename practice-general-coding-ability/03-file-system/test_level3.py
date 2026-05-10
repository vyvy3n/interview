"""
Level 3 tests — run with: python test_level3.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_register_new_user():
    queries = [["USER_REGISTER", "1", "alice", "1000"]]
    assert solution(queries) == ["true"]


def test_register_duplicate_user_returns_false():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "alice", "500"],
    ]
    assert solution(queries) == ["true", "false"]


def test_user_upload_returns_remaining_capacity():
    # alice cap=1000, upload 300 → used=300, rem=700
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "doc.txt", "300"],
    ]
    assert solution(queries) == ["true", "700"]


def test_user_upload_unknown_user_returns_empty():
    queries = [["USER_UPLOAD", "1", "ghost", "file.txt", "100"]]
    assert solution(queries) == [""]


def test_user_upload_name_conflict_with_admin_file():
    # FILE_UPLOAD creates an admin file; USER_UPLOAD with same name must fail.
    queries = [
        ["FILE_UPLOAD",   "1", "shared.pdf",        "999"],
        ["USER_REGISTER", "2", "alice",              "1000"],
        ["USER_UPLOAD",   "3", "alice", "shared.pdf", "50"],
    ]
    assert solution(queries) == ["true", "true", ""]


def test_user_upload_name_conflict_with_other_user():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "1000"],
        ["USER_UPLOAD",   "3", "alice", "file.txt", "100"],  # alice: used=100, rem=900
        ["USER_UPLOAD",   "4", "bob",   "file.txt", "200"],  # conflict with alice's file
    ]
    assert solution(queries) == ["true", "true", "900", ""]


def test_user_upload_capacity_exactly_fits():
    # Uploading exactly the remaining capacity → returns "0"
    queries = [
        ["USER_REGISTER", "1", "alice", "500"],
        ["USER_UPLOAD",   "2", "alice", "big.bin", "500"],
    ]
    assert solution(queries) == ["true", "0"]


def test_user_upload_exceeds_capacity_by_one():
    queries = [
        ["USER_REGISTER", "1", "alice", "500"],
        ["USER_UPLOAD",   "2", "alice", "big.bin", "501"],
    ]
    assert solution(queries) == ["true", ""]


def test_user_upload_multiple_files_accumulates():
    # alice cap=1000: upload 300 (rem=700), then 400 (rem=300), then 400 (exceeds)
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "a.txt", "300"],  # rem=700
        ["USER_UPLOAD",   "3", "alice", "b.txt", "400"],  # rem=300
        ["USER_UPLOAD",   "4", "alice", "c.txt", "400"],  # 300+400+400=1100 > 1000 → ""
    ]
    assert solution(queries) == ["true", "700", "300", ""]


def test_user_get_own_file():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "doc.txt", "250"],
        ["USER_GET",      "3", "alice", "doc.txt"],
    ]
    assert solution(queries) == ["true", "750", "250"]


def test_user_get_other_users_file_returns_empty():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "1000"],
        ["USER_UPLOAD",   "3", "alice", "secret.txt", "100"],
        ["USER_GET",      "4", "bob",   "secret.txt"],   # bob doesn't own it
    ]
    assert solution(queries) == ["true", "true", "900", ""]


def test_user_get_missing_file_returns_empty():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_GET",      "2", "alice", "nonexistent.txt"],
    ]
    assert solution(queries) == ["true", ""]


def test_user_copy_to_new_name():
    # alice: upload doc.txt(300) → rem=700. Copy → doc2.txt(300) → used=600, rem=400
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "doc.txt",  "300"],   # rem=700
        ["USER_COPY",     "3", "alice", "doc.txt",  "doc2.txt"],  # rem=400
        ["USER_GET",      "4", "alice", "doc2.txt"],
    ]
    assert solution(queries) == ["true", "700", "400", "300"]


def test_user_copy_overwrites_own_file():
    # alice: a(300) + b(100) = used=400, rem=600.
    # Copy a → b: free old b(100), add a(300). net +200. used=600, rem=400.
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_UPLOAD",   "2", "alice", "a.txt", "300"],   # rem=700
        ["USER_UPLOAD",   "3", "alice", "b.txt", "100"],   # rem=600
        ["USER_COPY",     "4", "alice", "a.txt", "b.txt"],  # overwrite: used=600, rem=400
        ["USER_GET",      "5", "alice", "b.txt"],
    ]
    assert solution(queries) == ["true", "700", "600", "400", "300"]


def test_user_copy_dest_owned_by_other_fails():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "1000"],
        ["USER_UPLOAD",   "3", "alice", "src.txt", "100"],
        ["USER_UPLOAD",   "4", "bob",   "dst.txt", "200"],
        ["USER_COPY",     "5", "alice", "src.txt", "dst.txt"],  # dst owned by bob
    ]
    assert solution(queries) == ["true", "true", "900", "800", ""]


def test_user_copy_source_not_owned_fails():
    queries = [
        ["USER_REGISTER", "1", "alice", "1000"],
        ["USER_REGISTER", "2", "bob",   "1000"],
        ["USER_UPLOAD",   "3", "alice", "alice_file.txt", "100"],
        ["USER_COPY",     "4", "bob",   "alice_file.txt", "copy.txt"],  # not bob's
    ]
    assert solution(queries) == ["true", "true", "900", ""]


def test_user_copy_would_exceed_capacity_fails():
    # alice cap=400. owns a.txt(300). Copy a → b would make used=600 > 400.
    queries = [
        ["USER_REGISTER", "1", "alice", "400"],
        ["USER_UPLOAD",   "2", "alice", "a.txt", "300"],   # rem=100
        ["USER_COPY",     "3", "alice", "a.txt", "b.txt"],  # would need 300 more, only 100 left
    ]
    assert solution(queries) == ["true", "100", ""]


def test_user_search_own_files_only():
    queries = [
        ["USER_REGISTER", "1", "alice", "2000"],
        ["USER_REGISTER", "2", "bob",   "2000"],
        ["USER_UPLOAD",   "3", "alice", "doc_alice.txt",  "300"],
        ["USER_UPLOAD",   "4", "bob",   "doc_bob.txt",    "400"],
        ["USER_SEARCH",   "5", "alice", "doc"],
    ]
    # alice only owns doc_alice.txt
    assert solution(queries) == ["true", "true", "1700", "1600", "doc_alice.txt(300)"]


def test_user_search_unknown_user_returns_empty():
    queries = [
        ["FILE_UPLOAD",  "1", "file.txt", "100"],
        ["USER_SEARCH",  "2", "ghost",    "file"],
    ]
    assert solution(queries) == ["true", ""]


def test_l1_l2_ops_still_work():
    # FILE_UPLOAD, FILE_GET, FILE_COPY, FILE_SEARCH must coexist with user ops.
    queries = [
        ["FILE_UPLOAD",   "1", "admin_file.txt", "999"],
        ["USER_REGISTER", "2", "alice",           "1000"],
        ["USER_UPLOAD",   "3", "alice", "alice_doc.txt", "200"],  # rem=800
        ["FILE_SEARCH",   "4", ""],   # should see both admin_file and alice_doc
        ["FILE_GET",      "5", "alice_doc.txt"],   # returns size regardless of owner
    ]
    result = solution(queries)
    assert result[0] == "true"
    assert result[1] == "true"
    assert result[2] == "800"
    # FILE_SEARCH shows all files: admin_file(999) > alice_doc(200)
    assert result[3] == "admin_file.txt(999), alice_doc.txt(200)"
    assert result[4] == "200"


def test_spec_worked_example():
    queries = [
        ["USER_REGISTER", "1",  "alice",  "1000"],
        ["USER_REGISTER", "2",  "bob",    "500"],
        ["USER_REGISTER", "3",  "alice",  "999"],
        ["USER_UPLOAD",   "4",  "alice",  "doc.txt",    "300"],
        ["USER_UPLOAD",   "5",  "bob",    "doc.txt",    "100"],
        ["USER_UPLOAD",   "6",  "bob",    "img.png",    "200"],
        ["FILE_UPLOAD",   "7",  "shared.pdf",           "999"],
        ["USER_UPLOAD",   "8",  "alice",  "shared.pdf", "10"],
        ["USER_GET",      "9",  "alice",  "doc.txt"],
        ["USER_GET",      "10", "bob",    "doc.txt"],
        ["USER_COPY",     "11", "alice",  "doc.txt",    "doc2.txt"],
        ["USER_COPY",     "12", "bob",    "doc.txt",    "img2.png"],
        ["USER_SEARCH",   "13", "alice",  "doc"],
        ["USER_SEARCH",   "14", "bob",    ""],
    ]
    assert solution(queries) == [
        "true", "true", "false",
        "700", "",
        "300",
        "true", "",
        "300", "",
        "400", "",
        "doc.txt(300), doc2.txt(300)",
        "img.png(200)",
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
