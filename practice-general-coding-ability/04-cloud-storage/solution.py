"""
Cloud Storage System.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md first. Each level's spec is in spec/levelN.md.

Data model:
  users   = {}   # user_id (str) -> {"quota": int, "used": int, "files": {file_id: size}}
  shares  = {}   # (owner_id, file_id) -> set of recipient_ids   [L3]
  shared_with = {}  # recipient_id -> set of (owner_id, file_id) [L3, reverse index]
  backups = {}   # backup_id (str) -> {"user_id": str, "files": {...}, "out": ..., "in": ...}
  backup_counter = [0]  # global int wrapped in list for mutation from inner scope [L4]
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

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def remove_all_shares_for_file(owner_id, file_id):
        """Remove all outgoing shares for (owner_id, file_id); update shared_with."""
        key = (owner_id, file_id)
        if key in shares:
            for recip in shares[key]:
                shared_with.get(recip, set()).discard(key)
            del shares[key]

    def remove_all_incoming_shares_for_user(user_id):
        """Remove all shares received by user_id; update shares (forward index)."""
        for key in list(shared_with.get(user_id, set())):
            shares.get(key, set()).discard(user_id)
        shared_with.pop(user_id, None)

    def remove_all_outgoing_shares_for_user(user_id):
        """Remove all shares where user_id is the owner."""
        to_remove = [k for k in shares if k[0] == user_id]
        for key in to_remove:
            for recip in shares[key]:
                shared_with.get(recip, set()).discard(key)
            del shares[key]

    # ------------------------------------------------------------------ #
    # LEVEL 1                                                              #
    # ------------------------------------------------------------------ #

    for q in queries:
        op = q[0]

        if op == "CREATE_USER":
            _, _ts, user_id, quota = q
            if user_id in users:
                out.append("false")
            else:
                users[user_id] = {"quota": int(quota), "used": 0, "files": {}}
                out.append("true")

        elif op == "UPLOAD":
            _, _ts, user_id, file_id, size = q
            if user_id not in users:
                out.append("")
                continue
            u = users[user_id]
            new_size = int(size)
            old_size = u["files"].get(file_id, 0)
            delta = new_size - old_size
            if u["used"] + delta > u["quota"]:
                out.append("")
            else:
                u["files"][file_id] = new_size
                u["used"] += delta
                out.append(str(u["used"]))

        elif op == "DELETE":
            _, _ts, user_id, file_id = q
            if user_id not in users:
                out.append("false")
                continue
            u = users[user_id]
            if file_id not in u["files"]:
                out.append("false")
            else:
                u["used"] -= u["files"].pop(file_id)
                # L3: cascade all shares attached to this (owner, file)
                remove_all_shares_for_file(user_id, file_id)
                out.append("true")

        # ------------------------------------------------------------------ #
        # LEVEL 2                                                              #
        # ------------------------------------------------------------------ #

        elif op == "GET_USAGE":
            _, _ts, user_id = q
            if user_id not in users:
                out.append("")
            else:
                u = users[user_id]
                out.append(f"{u['used']}/{u['quota']}")

        elif op == "TOP_K_USERS":
            _, _ts, k = q
            k = int(k)
            if not users:
                out.append("")
            else:
                ranked = sorted(
                    users.items(),
                    key=lambda kv: (-kv[1]["used"], kv[0])
                )[:k]
                parts = [f"{uid}({u['used']}/{u['quota']})" for uid, u in ranked]
                out.append(", ".join(parts))

        # ------------------------------------------------------------------ #
        # LEVEL 3                                                              #
        # ------------------------------------------------------------------ #

        elif op == "SHARE":
            _, _ts, owner, file_id, recip = q
            if (owner not in users
                    or file_id not in users[owner]["files"]
                    or recip not in users
                    or owner == recip):
                out.append("")
                continue
            key = (owner, file_id)
            if recip in shares.get(key, set()):
                out.append("")
                continue
            shares.setdefault(key, set()).add(recip)
            shared_with.setdefault(recip, set()).add(key)
            out.append("true")

        elif op == "UNSHARE":
            _, _ts, owner, file_id, recip = q
            key = (owner, file_id)
            if recip not in shares.get(key, set()):
                out.append("")
            else:
                shares[key].discard(recip)
                shared_with.get(recip, set()).discard(key)
                out.append("true")

        elif op == "LIST_SHARED_WITH":
            _, _ts, user_id = q
            items = shared_with.get(user_id, set())
            if not items:
                out.append("")
            else:
                sorted_items = sorted(items, key=lambda t: (t[0], t[1]))
                out.append(", ".join(f"{owner}:{fid}" for owner, fid in sorted_items))

        # ------------------------------------------------------------------ #
        # LEVEL 4                                                              #
        # ------------------------------------------------------------------ #

        elif op == "BACKUP":
            _, _ts, user_id = q
            if user_id not in users:
                out.append("")
                continue
            backup_counter[0] += 1
            bid = f"backup{backup_counter[0]}"
            u = users[user_id]
            # Deep-copy files
            files_snap = dict(u["files"])
            # Snapshot outgoing shares: (owner, file_id) -> frozenset of recipients
            out_snap = {
                k: set(v)
                for k, v in shares.items()
                if k[0] == user_id
            }
            # Snapshot incoming shares: set of (owner, file_id) tuples
            in_snap = set(shared_with.get(user_id, set()))
            backups[bid] = {
                "user_id": user_id,
                "files": files_snap,
                "out": out_snap,   # {(owner, file_id): set_of_recipients}
                "in": in_snap,     # set of (owner, file_id)
            }
            out.append(bid)

        elif op == "RESTORE":
            _, _ts, user_id, backup_id = q
            # Step 1: backup must exist and belong to user_id
            if backup_id not in backups or backups[backup_id]["user_id"] != user_id:
                out.append("")
                continue
            # Step 2: total size of backup files must fit in current quota
            if user_id not in users:
                out.append("")
                continue
            snap = backups[backup_id]
            total_size = sum(snap["files"].values())
            u = users[user_id]
            if total_size > u["quota"]:
                out.append("")
                continue
            # Steps 3-8: apply atomically
            # 3. Remove current files
            u["files"] = {}
            u["used"] = 0
            # 4. Remove current outgoing shares from this user
            remove_all_outgoing_shares_for_user(user_id)
            # 5. Remove current incoming shares to this user
            remove_all_incoming_shares_for_user(user_id)
            # 6. Restore files
            u["files"] = dict(snap["files"])
            u["used"] = total_size
            # 7. Restore outgoing shares — only if recipient still exists
            for (owner, fid), recips in snap["out"].items():
                for recip in recips:
                    if recip in users:
                        key = (owner, fid)
                        shares.setdefault(key, set()).add(recip)
                        shared_with.setdefault(recip, set()).add(key)
            # 8. Restore incoming shares — only if original owner still exists
            #    AND still owns that file
            for (owner, fid) in snap["in"]:
                if (owner in users
                        and fid in users[owner]["files"]):
                    key = (owner, fid)
                    shares.setdefault(key, set()).add(user_id)
                    shared_with.setdefault(user_id, set()).add(key)
            out.append("true")

        elif op == "TRANSFER_OWNERSHIP":
            _, _ts, from_user, to_user = q
            # Validate
            if from_user not in users or to_user not in users or from_user == to_user:
                out.append("")
                continue
            fu = users[from_user]
            tu = users[to_user]
            # Quota check accounting for collisions
            collision_size = sum(
                tu["files"][fid]
                for fid in fu["files"]
                if fid in tu["files"]
            )
            if tu["used"] - collision_size + fu["used"] > tu["quota"]:
                out.append("")
                continue
            # Merge files: from_user's files overwrite to_user's on collision
            for fid, size in fu["files"].items():
                if fid in tu["files"]:
                    tu["used"] -= tu["files"][fid]  # remove old colliding size
                tu["files"][fid] = size
                tu["used"] += size
            # Re-anchor outgoing shares: (from_user, fid) -> (to_user, fid)
            from_keys = [k for k in shares if k[0] == from_user]
            for old_key in from_keys:
                _, fid = old_key
                new_key = (to_user, fid)
                recips = shares.pop(old_key)
                # Merge into to_user's share key (in case to_user also shared same file)
                existing = shares.setdefault(new_key, set())
                for recip in recips:
                    existing.add(recip)
                    # Update reverse index: swap old_key for new_key
                    sw = shared_with.get(recip, set())
                    sw.discard(old_key)
                    sw.add(new_key)
                    shared_with[recip] = sw
            # Remove incoming shares TO from_user (they lose their identity)
            remove_all_incoming_shares_for_user(from_user)
            # Remove from_user and their backups
            del users[from_user]
            for bid in list(backups.keys()):
                if backups[bid]["user_id"] == from_user:
                    del backups[bid]
            out.append("true")

        else:
            raise ValueError(f"Unknown operation: {op!r}")

    return out
