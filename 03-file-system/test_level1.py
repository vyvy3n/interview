"""
Level 1 tests — run with: python test_level1.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_upload_single_file():
    queries = [["FILE_UPLOAD", "1", "notes.txt", "100"]]
    assert solution(queries) == ["true"]


def test_upload_duplicate_returns_false():
    queries = [
        ["FILE_UPLOAD", "1", "notes.txt", "100"],
        ["FILE_UPLOAD", "2", "notes.txt", "200"],   # duplicate
    ]
    assert solution(queries) == ["true", "false"]


def test_upload_duplicate_does_not_overwrite():
    # After a duplicate upload attempt, the original size must be preserved.
    queries = [
        ["FILE_UPLOAD", "1", "notes.txt", "100"],
        ["FILE_UPLOAD", "2", "notes.txt", "999"],   # rejected
        ["FILE_GET",    "3", "notes.txt"],
    ]
    assert solution(queries) == ["true", "false", "100"]


def test_get_existing_file():
    queries = [
        ["FILE_UPLOAD", "1", "report.pdf", "500"],
        ["FILE_GET",    "2", "report.pdf"],
    ]
    assert solution(queries) == ["true", "500"]


def test_get_missing_file_returns_empty():
    queries = [["FILE_GET", "1", "ghost.txt"]]
    assert solution(queries) == [""]


def test_get_multiple_files_independently():
    queries = [
        ["FILE_UPLOAD", "1", "a.txt", "10"],
        ["FILE_UPLOAD", "2", "b.txt", "20"],
        ["FILE_GET",    "3", "a.txt"],
        ["FILE_GET",    "4", "b.txt"],
        ["FILE_GET",    "5", "c.txt"],   # missing
    ]
    assert solution(queries) == ["true", "true", "10", "20", ""]


def test_copy_to_new_name():
    queries = [
        ["FILE_UPLOAD", "1", "original.txt", "300"],
        ["FILE_COPY",   "2", "original.txt", "copy.txt"],
        ["FILE_GET",    "3", "copy.txt"],
    ]
    assert solution(queries) == ["true", "true", "300"]


def test_copy_overwrites_existing_dest():
    queries = [
        ["FILE_UPLOAD", "1", "src.txt",    "300"],
        ["FILE_UPLOAD", "2", "target.txt", "999"],
        ["FILE_COPY",   "3", "src.txt",    "target.txt"],   # overwrite
        ["FILE_GET",    "4", "target.txt"],
    ]
    assert solution(queries) == ["true", "true", "true", "300"]


def test_copy_missing_source_returns_empty():
    queries = [["FILE_COPY", "1", "ghost.txt", "dest.txt"]]
    assert solution(queries) == [""]


def test_copy_missing_source_leaves_dest_unchanged():
    queries = [
        ["FILE_UPLOAD", "1", "existing.txt", "50"],
        ["FILE_COPY",   "2", "ghost.txt",    "existing.txt"],   # source missing
        ["FILE_GET",    "3", "existing.txt"],                    # unchanged
    ]
    assert solution(queries) == ["true", "", "50"]


def test_source_unchanged_after_copy():
    # Copying should not remove or alter the source.
    queries = [
        ["FILE_UPLOAD", "1", "src.txt",  "200"],
        ["FILE_COPY",   "2", "src.txt",  "dst.txt"],
        ["FILE_GET",    "3", "src.txt"],
        ["FILE_GET",    "4", "dst.txt"],
    ]
    assert solution(queries) == ["true", "true", "200", "200"]


def test_upload_after_copy_is_rejected():
    # After copy, the dest name already exists — a fresh upload must fail.
    queries = [
        ["FILE_UPLOAD", "1", "src.txt", "100"],
        ["FILE_COPY",   "2", "src.txt", "dst.txt"],
        ["FILE_UPLOAD", "3", "dst.txt", "999"],   # dst already exists via copy
    ]
    assert solution(queries) == ["true", "true", "false"]


def test_full_sequence_from_spec():
    queries = [
        ["FILE_UPLOAD", "1", "report.pdf",   "500"],
        ["FILE_UPLOAD", "2", "report.pdf",   "300"],   # duplicate
        ["FILE_GET",    "3", "report.pdf"],
        ["FILE_GET",    "4", "missing.txt"],
        ["FILE_COPY",   "5", "report.pdf",   "backup.pdf"],
        ["FILE_COPY",   "6", "ghost.txt",    "ghost2.txt"],
        ["FILE_UPLOAD", "7", "notes.txt",    "100"],
        ["FILE_COPY",   "8", "notes.txt",    "backup.pdf"],   # overwrite
        ["FILE_GET",    "9", "backup.pdf"],
    ]
    assert solution(queries) == [
        "true", "false", "500", "", "true", "", "true", "true", "100",
    ]


def test_large_size_no_overflow():
    queries = [
        ["FILE_UPLOAD", "1", "bigfile.bin", "9999999999999"],
        ["FILE_GET",    "2", "bigfile.bin"],
    ]
    assert solution(queries) == ["true", "9999999999999"]


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
