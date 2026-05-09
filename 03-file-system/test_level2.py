"""
Level 2 tests — run with: python test_level2.py

No external deps. Uses only the standard library so you can run it anywhere.
"""

import sys
import traceback
from solution import solution


# ----- Test cases -----


def test_search_single_match():
    queries = [
        ["FILE_UPLOAD", "1", "report.pdf", "500"],
        ["FILE_SEARCH", "2", "rep"],
    ]
    assert solution(queries) == ["true", "report.pdf(500)"]


def test_search_no_match_returns_empty():
    queries = [
        ["FILE_UPLOAD", "1", "report.pdf", "500"],
        ["FILE_SEARCH", "2", "xyz"],
    ]
    assert solution(queries) == ["true", ""]


def test_search_empty_prefix_matches_all():
    queries = [
        ["FILE_UPLOAD", "1", "alpha.txt", "100"],
        ["FILE_UPLOAD", "2", "beta.txt",  "200"],
        ["FILE_SEARCH", "3", ""],
    ]
    # Size desc: beta(200), alpha(100)
    assert solution(queries) == ["true", "true", "beta.txt(200), alpha.txt(100)"]


def test_search_sorted_size_desc():
    queries = [
        ["FILE_UPLOAD", "1", "small.txt",  "10"],
        ["FILE_UPLOAD", "2", "medium.txt", "50"],
        ["FILE_UPLOAD", "3", "large.txt",  "200"],
        ["FILE_SEARCH", "4", ""],
    ]
    assert solution(queries) == [
        "true", "true", "true",
        "large.txt(200), medium.txt(50), small.txt(10)",
    ]


def test_search_ties_broken_by_name_asc():
    queries = [
        ["FILE_UPLOAD", "1", "beta.txt",  "300"],
        ["FILE_UPLOAD", "2", "alpha.txt", "300"],   # same size
        ["FILE_UPLOAD", "3", "gamma.txt", "300"],   # same size
        ["FILE_SEARCH", "4", ""],
    ]
    # All size 300 → sort by name asc: alpha, beta, gamma
    assert solution(queries) == [
        "true", "true", "true",
        "alpha.txt(300), beta.txt(300), gamma.txt(300)",
    ]


def test_search_mixed_sizes_and_ties():
    queries = [
        ["FILE_UPLOAD", "1", "alpha.txt",  "300"],
        ["FILE_UPLOAD", "2", "alpha.md",   "300"],   # tie with alpha.txt
        ["FILE_UPLOAD", "3", "beta.txt",   "500"],
        ["FILE_UPLOAD", "4", "alphabet",   "100"],
        ["FILE_UPLOAD", "5", "gamma.txt",  "200"],
        ["FILE_SEARCH", "6", "alpha"],
    ]
    # Candidates: alpha.txt(300), alpha.md(300), alphabet(100)
    # Sort: 300 > 300 > 100; tie at 300: alpha.md < alpha.txt
    assert solution(queries) == [
        "true", "true", "true", "true", "true",
        "alpha.md(300), alpha.txt(300), alphabet(100)",
    ]


def test_search_prefix_case_sensitive():
    queries = [
        ["FILE_UPLOAD", "1", "Report.pdf", "500"],
        ["FILE_SEARCH", "2", "report"],   # lowercase — no match
        ["FILE_SEARCH", "3", "Report"],   # exact match
    ]
    assert solution(queries) == ["true", "", "Report.pdf(500)"]


def test_search_returns_at_most_10():
    # Upload 12 files all with prefix "file"
    uploads = [
        ["FILE_UPLOAD", str(i), f"file{i:02d}.txt", str(i * 10)]
        for i in range(1, 13)
    ]
    search = [["FILE_SEARCH", "100", "file"]]
    queries = uploads + search
    result = solution(queries)
    search_result = result[-1]
    # Must have exactly 10 entries
    entries = search_result.split(", ")
    assert len(entries) == 10, f"Expected 10 results, got {len(entries)}: {search_result}"


def test_search_top10_are_largest():
    # Upload files with sizes 10, 20, ..., 120 (12 files)
    # Top 10 should be sizes 120, 110, ..., 30 (the ten largest)
    uploads = [
        ["FILE_UPLOAD", str(i), f"file{i:02d}.txt", str(i * 10)]
        for i in range(1, 13)
    ]
    search = [["FILE_SEARCH", "100", "file"]]
    result = solution(uploads + search)
    search_result = result[-1]
    # Extract sizes from result
    entries = search_result.split(", ")
    sizes = [int(e.split("(")[1].rstrip(")")) for e in entries]
    assert sizes == sorted(sizes, reverse=True), "Results not sorted by size descending"
    assert sizes[0] == 120
    assert sizes[-1] == 30   # 11th-smallest (size 20) and 12th (size 10) are excluded


def test_search_exact_prefix_match():
    # Prefix "report" should NOT match "reporter" wait — actually it should.
    # "reporter".startswith("report") == True. Let's test that it does match.
    queries = [
        ["FILE_UPLOAD", "1", "report.pdf",   "100"],
        ["FILE_UPLOAD", "2", "reporter.txt", "200"],
        ["FILE_UPLOAD", "3", "rep.md",       "300"],
        ["FILE_SEARCH", "4", "report"],
    ]
    # "report.pdf" and "reporter.txt" both start with "report"; "rep.md" does not
    assert solution(queries) == [
        "true", "true", "true",
        "reporter.txt(200), report.pdf(100)",
    ]


def test_search_after_copy_includes_copy():
    queries = [
        ["FILE_UPLOAD", "1", "doc.txt",    "400"],
        ["FILE_COPY",   "2", "doc.txt",    "doc_bak.txt"],
        ["FILE_SEARCH", "3", "doc"],
    ]
    # Both doc.txt and doc_bak.txt exist with size 400; tie → name asc
    assert solution(queries) == [
        "true", "true",
        "doc.txt(400), doc_bak.txt(400)",
    ]


def test_l1_ops_still_work_alongside_search():
    queries = [
        ["FILE_UPLOAD", "1", "a.txt",  "50"],
        ["FILE_SEARCH", "2", "a"],
        ["FILE_GET",    "3", "a.txt"],
        ["FILE_COPY",   "4", "a.txt",  "b.txt"],
        ["FILE_SEARCH", "5", ""],
    ]
    assert solution(queries) == [
        "true",
        "a.txt(50)",
        "50",
        "true",
        "a.txt(50), b.txt(50)",
    ]


def test_search_after_overwrite_reflects_new_size():
    queries = [
        ["FILE_UPLOAD", "1", "src.txt",  "800"],
        ["FILE_UPLOAD", "2", "dst.txt",  "100"],
        ["FILE_COPY",   "3", "src.txt",  "dst.txt"],   # dst overwritten to 800
        ["FILE_SEARCH", "4", "dst"],
    ]
    assert solution(queries) == ["true", "true", "true", "dst.txt(800)"]


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
