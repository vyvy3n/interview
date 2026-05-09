"""
Cloud Storage System.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md first. Each level's spec is in spec/levelN.md.

The skeleton below has the dispatch loop set up for all 4 levels.
Fill in each branch body. Delete the NotImplementedError as you go.

Data model hints:
  users   = {}   # user_id (str) -> {"quota": int, "used": int, "files": {file_id: size}}
  shares  = {}   # (owner_id, file_id) -> set of recipient_ids   [L3]
  shared_with = {}  # recipient_id -> set of (owner_id, file_id) [L3, reverse index]
  backups = {}   # backup_id (str) -> {"user_id": str, "files": {...}, "out": ..., "in": ...}
  backup_counter = 0  # global int, incremented each BACKUP call  [L4]
"""


def solution(queries):
    users = {}
    # L3 share indexes
    shares = {}       # (owner_id, file_id) -> set of recipient_ids
    shared_with = {}  # recipient_id -> set of (owner_id, file_id)
    # L4 backup state
    backups = {}
    backup_counter = [0]  # wrap in list so nested scopes can mutate it

    out = []

    for q in queries:
        op = q[0]

        # ------------------------------------------------------------------ #
        # LEVEL 1                                                              #
        # ------------------------------------------------------------------ #

        if op == "CREATE_USER":
            # q is ["CREATE_USER", timestamp, user_id, quota]
            _, timestamp, user_id, quota = q
            # TODO: create user with int(quota); return "true" if new, "false" if duplicate.
            raise NotImplementedError("CREATE_USER — see spec/level1.md §1")

        elif op == "UPLOAD":
            # q is ["UPLOAD", timestamp, user_id, file_id, size]
            _, timestamp, user_id, file_id, size = q
            # TODO: upload file; handle overwrite (quota diff); return str(used) or "".
            # Quota check: used + (new_size - old_size) <= quota.
            # On failure: return "" without modifying any state.
            raise NotImplementedError("UPLOAD — see spec/level1.md §2")

        elif op == "DELETE":
            # q is ["DELETE", timestamp, user_id, file_id]
            _, timestamp, user_id, file_id = q
            # TODO: delete file; free bytes; cascade shares (L3).
            # Return "true" if deleted, "false" if user or file missing.
            raise NotImplementedError("DELETE — see spec/level1.md §3")

        # ------------------------------------------------------------------ #
        # LEVEL 2                                                              #
        # ------------------------------------------------------------------ #

        elif op == "GET_USAGE":
            # q is ["GET_USAGE", timestamp, user_id]
            _, timestamp, user_id = q
            # TODO: return "<used>/<quota>" or "" if user missing.
            raise NotImplementedError("GET_USAGE — see spec/level2.md §1")

        elif op == "TOP_K_USERS":
            # q is ["TOP_K_USERS", timestamp, k]
            _, timestamp, k = q
            # TODO: sort all users by used DESC, user_id ASC for ties.
            # Format: "uid1(used/quota), uid2(used/quota), ..." — top int(k) users.
            # Return "" if no users exist.
            raise NotImplementedError("TOP_K_USERS — see spec/level2.md §2")

        # ------------------------------------------------------------------ #
        # LEVEL 3                                                              #
        # ------------------------------------------------------------------ #

        elif op == "SHARE":
            # q is ["SHARE", timestamp, owner_user, file_id, recipient_user]
            _, timestamp, owner_user, file_id, recipient_user = q
            # TODO: validate (owner exists, file exists, recipient exists, not self, not dup).
            # Add to shares[(owner_user, file_id)] and shared_with[recipient_user].
            # Return "true" or "".
            raise NotImplementedError("SHARE — see spec/level3.md §1")

        elif op == "UNSHARE":
            # q is ["UNSHARE", timestamp, owner_user, file_id, recipient_user]
            _, timestamp, owner_user, file_id, recipient_user = q
            # TODO: remove share if it exists; return "true" or "".
            raise NotImplementedError("UNSHARE — see spec/level3.md §2")

        elif op == "LIST_SHARED_WITH":
            # q is ["LIST_SHARED_WITH", timestamp, user_id]
            _, timestamp, user_id = q
            # TODO: collect all (owner, file_id) pairs from shared_with[user_id].
            # Sort by owner ASC then file_id ASC.
            # Format: "owner:file_id, owner:file_id, ..."
            # Return "" if nothing shared with this user.
            raise NotImplementedError("LIST_SHARED_WITH — see spec/level3.md §3")

        # ------------------------------------------------------------------ #
        # LEVEL 4                                                              #
        # ------------------------------------------------------------------ #

        elif op == "BACKUP":
            # q is ["BACKUP", timestamp, user_id]
            _, timestamp, user_id = q
            # TODO: increment backup_counter[0]; generate backup_id = f"backup{counter}".
            # Deep-copy user's files dict and share state (outgoing + incoming).
            # Store in backups[backup_id] = {"user_id": ..., "files": {...}, "out": ..., "in": ...}.
            # Return backup_id or "" if user missing.
            raise NotImplementedError("BACKUP — see spec/level4.md §1")

        elif op == "RESTORE":
            # q is ["RESTORE", timestamp, user_id, backup_id]
            _, timestamp, user_id, backup_id = q
            # TODO (all-or-nothing):
            #   1. Verify backup_id exists and belongs to user_id — else return "".
            #   2. Verify sum of backup file sizes <= user's current quota — else return "".
            #   3. Remove all current files (update used=0).
            #   4. Remove all current outgoing shares from this user.
            #   5. Remove all current incoming shares to this user.
            #   6. Restore files from backup.
            #   7. Restore outgoing shares — only if recipient still exists.
            #   8. Restore incoming shares — only if original owner still exists and owns that file.
            # Return "true" or "".
            raise NotImplementedError("RESTORE — see spec/level4.md §2")

        elif op == "TRANSFER_OWNERSHIP":
            # q is ["TRANSFER_OWNERSHIP", timestamp, from_user, to_user]
            _, timestamp, from_user, to_user = q
            # TODO:
            #   1. Validate both users exist and from_user != to_user.
            #   2. Quota check: to_user.quota >= to_user.used - collision_sizes + from_user.used.
            #      (collision = file_id exists in BOTH users; to_user's copy is overwritten)
            #   3. Merge files: copy all from_user files into to_user (overwrite on collision).
            #   4. Re-anchor outgoing shares: change owner from from_user to to_user in shares + shared_with.
            #   5. Remove from_user (including their backups).
            # Return "true" or "".
            raise NotImplementedError("TRANSFER_OWNERSHIP — see spec/level4.md §3")

        else:
            raise ValueError(f"Unknown operation: {op!r}")

    return out
