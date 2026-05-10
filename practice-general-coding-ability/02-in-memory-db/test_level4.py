"""
Level 4 tests — run with: python test_level4.py

Tests BACKUP and RESTORE on top of all Level 1-3 operations.
No external deps. Uses only the standard library.
"""

import sys
import traceback
from solution import solution


# ----- Level 1-3 regression -----


def test_l1_still_works_after_no_backup():
    queries = [
        ["SET", "1", "k", "f", "v"],
        ["GET", "2", "k", "f"],
    ]
    assert solution(queries) == ["", "v"]


def test_l3_ttl_still_works():
    # Sanity: TTL still works in presence of backup-related code
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val", "5"],
        ["GET",          "14", "k", "f"],
        ["GET",          "15", "k", "f"],
    ]
    assert solution(queries) == ["", "val", ""]


# ----- BACKUP basics -----


def test_backup_empty_db_returns_zero():
    queries = [["BACKUP", "1"]]
    assert solution(queries) == ["0"]


def test_backup_counts_all_non_expired_pairs():
    queries = [
        ["SET",    "1", "a", "x", "1"],
        ["SET",    "2", "a", "y", "2"],
        ["SET",    "3", "b", "z", "3"],
        ["BACKUP", "4"],
    ]
    assert solution(queries) == ["", "", "", "3"]


def test_backup_excludes_expired_entries():
    # a.x expires at 15. BACKUP at ts=15 → a.x excluded.
    queries = [
        ["SET_WITH_TTL", "10", "a", "x", "v", "5"],  # expiry=15
        ["SET",          "11", "b", "y", "w"],
        ["BACKUP",       "15"],   # a.x expired at ts=15
    ]
    # Only b.y is non-expired at ts=15
    assert solution(queries) == ["", "", "1"]


def test_backup_excludes_deleted_entries():
    queries = [
        ["SET",    "1", "a", "x", "1"],
        ["SET",    "2", "a", "y", "2"],
        ["DELETE", "3", "a", "x"],
        ["BACKUP", "4"],
    ]
    assert solution(queries) == ["", "", "true", "1"]


# ----- RESTORE basics -----


def test_restore_nonexistent_backup_returns_empty_and_no_change():
    queries = [
        ["SET",     "1", "k", "f", "original"],
        ["RESTORE", "2", "99"],   # no backup at ts=99
        ["GET",     "3", "k", "f"],
    ]
    assert solution(queries) == ["", "", "original"]


def test_restore_replaces_state_completely():
    queries = [
        ["SET",     "1", "a", "x", "hello"],
        ["BACKUP",  "2"],
        ["SET",     "3", "a", "x", "CHANGED"],
        ["SET",     "4", "b", "y", "new"],
        ["RESTORE", "5", "2"],
        ["GET",     "6", "a", "x"],   # back to hello
        ["GET",     "6", "b", "y"],   # gone — not in backup
    ]
    assert solution(queries) == ["", "1", "", "", "", "hello", ""]


def test_restore_wipes_entries_not_in_backup():
    queries = [
        ["SET",     "1", "a", "x", "keep"],
        ["BACKUP",  "2"],
        ["SET",     "3", "c", "z", "extra"],
        ["RESTORE", "4", "2"],
        ["GET",     "5", "c", "z"],   # must be gone
    ]
    assert solution(queries) == ["", "1", "", "", ""]


# ----- RESTORE with TTL re-anchoring -----


def test_restore_reanchors_ttl():
    # SET_WITH_TTL at ts=10, ttl=20 → expiry=30.
    # BACKUP at ts=15 → remaining_ttl = 30 - 15 = 15.
    # RESTORE at ts=50 → new expiry = 50 + 15 = 65.
    # GET at ts=64 → valid; GET at ts=65 → expired.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val", "20"],  # expiry=30
        ["BACKUP",       "15"],                           # remaining=15, count=1
        ["SET",          "20", "k", "f", "overwrite"],  # overwrite after backup
        ["RESTORE",      "50", "15"],                    # re-anchor: expiry=50+15=65
        ["GET",          "64", "k", "f"],                # valid
        ["GET",          "65", "k", "f"],                # expired
    ]
    assert solution(queries) == ["", "1", "", "", "val", ""]


def test_restore_no_ttl_entries_stay_no_ttl():
    # Plain SET entry in backup → after RESTORE it should still never expire.
    queries = [
        ["SET",     "1", "k", "f", "forever"],
        ["BACKUP",  "2"],
        ["RESTORE", "100", "2"],
        ["GET",     "999", "k", "f"],   # should still be there
    ]
    assert solution(queries) == ["", "1", "", "forever"]


def test_restore_ttl_expired_at_backup_time_not_in_snapshot():
    # Entry expires at ts=15. BACKUP at ts=20 → entry already expired → not in snapshot.
    # After RESTORE, entry must not exist.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val", "5"],  # expiry=15
        ["SET",          "11", "k", "g", "other"],
        ["BACKUP",       "20"],   # k.f expired, only k.g in snapshot → count=1
        ["RESTORE",      "30", "20"],
        ["GET",          "31", "k", "f"],   # was expired at backup time, not restored
        ["GET",          "31", "k", "g"],   # was in snapshot
    ]
    assert solution(queries) == ["", "", "1", "", "", "other"]


# ----- RESTORE + L1-L3 ops work on restored state -----


def test_l1_ops_work_on_restored_state():
    queries = [
        ["SET",     "1", "a", "x", "original"],
        ["BACKUP",  "2"],
        ["SET",     "3", "a", "x", "mutated"],
        ["RESTORE", "4", "2"],
        # Now state is {a: {x: original}}
        ["SET",     "5", "a", "x", "post_restore"],
        ["GET",     "6", "a", "x"],
        ["DELETE",  "7", "a", "x"],
        ["GET",     "8", "a", "x"],
    ]
    assert solution(queries) == ["", "1", "", "", "", "post_restore", "true", ""]


def test_scan_on_restored_state():
    queries = [
        ["SET",     "1", "row", "b", "2"],
        ["SET",     "2", "row", "a", "1"],
        ["BACKUP",  "3"],
        ["SET",     "4", "row", "c", "3"],  # add extra field after backup
        ["RESTORE", "5", "3"],
        ["SCAN",    "6", "row"],             # only a, b — not c
    ]
    assert solution(queries) == ["", "", "2", "", "", "a(1), b(2)"]


def test_set_with_ttl_on_restored_state():
    queries = [
        ["SET",          "1", "a", "x", "v"],
        ["BACKUP",       "2"],
        ["RESTORE",      "10", "2"],
        ["SET_WITH_TTL", "11", "a", "x", "ttl_val", "5"],  # expiry=16
        ["GET",          "15", "a", "x"],   # valid
        ["GET",          "16", "a", "x"],   # expired
    ]
    assert solution(queries) == ["", "1", "", "", "ttl_val", ""]


# ----- Multiple backups -----


def test_multiple_backups_independent():
    queries = [
        ["SET",     "1", "k", "f", "v1"],
        ["BACKUP",  "2"],                   # snapshot with v1
        ["SET",     "3", "k", "f", "v2"],
        ["BACKUP",  "4"],                   # snapshot with v2
        ["RESTORE", "5", "2"],              # restore v1
        ["GET",     "6", "k", "f"],
        ["RESTORE", "7", "4"],              # restore v2
        ["GET",     "8", "k", "f"],
    ]
    assert solution(queries) == ["", "1", "", "1", "", "v1", "", "v2"]


def test_can_restore_same_backup_twice():
    queries = [
        ["SET",     "1", "k", "f", "snap"],
        ["BACKUP",  "2"],
        ["SET",     "3", "k", "f", "changed"],
        ["RESTORE", "4", "2"],
        ["GET",     "5", "k", "f"],
        ["SET",     "6", "k", "f", "again"],
        ["RESTORE", "7", "2"],   # restore same backup a second time
        ["GET",     "8", "k", "f"],
    ]
    assert solution(queries) == ["", "1", "", "", "snap", "", "", "snap"]


# ----- TTL re-anchoring edge cases -----


def test_restore_with_zero_remaining_ttl_is_immediately_expired():
    # remaining_ttl = 0 would mean expiry = restore_ts + 0 = restore_ts.
    # At the very next query (ts > restore_ts), it should be expired.
    # Set at ts=10, ttl=5 → expiry=15. BACKUP at ts=15 → remaining=0 (but entry IS expired at ts=15).
    # So entry should NOT appear in backup at all.
    queries = [
        ["SET_WITH_TTL", "10", "k", "f", "val", "5"],  # expiry=15
        ["BACKUP",       "15"],   # k.f is expired at ts=15 → NOT in snapshot
        ["RESTORE",      "20", "15"],
        ["GET",          "21", "k", "f"],   # not in snapshot, so ""
    ]
    assert solution(queries) == ["", "0", "", ""]


def test_large_combined_scenario():
    # Mix of plain and TTL entries, backup, mutations, restore
    queries = [
        ["SET",          "1",  "u", "name",  "alice"],
        ["SET",          "2",  "u", "role",  "admin"],
        ["SET_WITH_TTL", "3",  "u", "token", "abc", "20"],  # expiry=23
        ["SET",          "4",  "v", "name",  "bob"],
        ["BACKUP",       "5"],   # 4 pairs: u.name, u.role, u.token (remaining=18), v.name
        ["SET",          "6",  "u", "name",  "ALICE"],
        ["DELETE",       "7",  "v", "name"],
        ["SET",          "8",  "w", "x",     "new"],
        ["RESTORE",      "10", "5"],
        # After restore: u.name=alice, u.role=admin, u.token=abc (expiry=10+18=28), v.name=bob
        ["GET",          "11", "u", "name"],   # alice (restored)
        ["GET",          "11", "v", "name"],   # bob (restored)
        ["GET",          "11", "w", "x"],      # "" (not in backup)
        ["GET",          "27", "u", "token"],  # valid (expiry=28)
        ["GET",          "28", "u", "token"],  # expired
        ["SCAN",         "29", "u"],           # name, role only (token expired)
    ]
    assert solution(queries) == [
        "", "", "", "", "4",
        "", "true", "",
        "",
        "alice", "bob", "", "abc", "", "name(alice), role(admin)",
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
        print(f"\033[32mAll {total} tests passed.\033[0m  Level 4 complete — all levels done!")
        return True
    print(f"\033[31m{len(failed)}/{total} failed.\033[0m  Keep going.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
