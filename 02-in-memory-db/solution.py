"""
In-Memory Key-Value-Field Database.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Internal state shape:
  db: Dict[str, Dict[str, tuple[str, int | None]]]
      key -> field -> (value, expiry_ts or None)

  backups: Dict[int, Dict[str, Dict[str, tuple[str, int | None]]]]
      backup_ts -> snapshot of db (with remaining_ttl stored instead of expiry)

Read spec/level1.md first, then level2.md, etc.

Each branch below:
  - Unpacks arguments by name
  - Raises NotImplementedError pointing to the relevant spec file
  - Has a comment noting the level

Delete each NotImplementedError line (and replace with your logic) as you
implement each level. Do not change the dispatch structure.
"""


def solution(queries):
    # State: key -> field -> (value, expiry_ts or None)
    # expiry_ts=None means the entry never expires.
    db = {}

    # Backups: backup_ts -> {key -> {field -> (value, remaining_ttl or None)}}
    # remaining_ttl=None means no TTL; remaining_ttl=R means R units left at backup time.
    backups = {}

    out = []

    for q in queries:
        op = q[0]

        # ------------------------------------------------------------------ #
        # LEVEL 1 — Basic reads/writes                                        #
        # ------------------------------------------------------------------ #

        if op == "SET":
            # q is ["SET", ts, key, field, value]
            _, ts, key, field, value = q
            # TODO: Store value at (key, field) with no TTL. Overwrite if exists.
            # Returns "".
            # See spec/level1.md
            # always overwrite
            if key not in db:
                db[key] = {}

            db[key][field] = (value, None)
            out.append("")

        elif op == "GET":
            # q is ["GET", ts, key, field]
            _, ts, key, field = q
            # TODO: Return the value at (key, field), or "" if missing or expired.
            # See spec/level1.md (expiry logic added in level3.md)
            if key in db and field in db[key]:
                out.append(db[key][field][0])
            else:
                out.append("")
        
        elif op == "DELETE":
            # q is ["DELETE", ts, key, field]
            _, ts, key, field = q
            # TODO: Remove (key, field). Return "true" if it existed (and not expired),
            # "false" otherwise.
            # See spec/level1.md (expiry logic added in level3.md)
            if key in db and field in db[key]:
                del db[key][field]
                out.append("true")
            else:
                out.append("false")

        # ------------------------------------------------------------------ #
        # LEVEL 2 — Scan operations                                           #
        # ------------------------------------------------------------------ #

        elif op == "SCAN":
            # q is ["SCAN", ts, key]
            _, ts, key = q
            # TODO: Return all non-expired (field, value) pairs at key, sorted
            # alphabetically by field, formatted as "f1(v1), f2(v2), ...".
            # Return "" if key missing or no non-expired fields.
            # See spec/level2.md
            raise NotImplementedError("SCAN — see spec/level2.md")

        elif op == "SCAN_BY_PREFIX":
            # q is ["SCAN_BY_PREFIX", ts, key, prefix]
            _, ts, key, prefix = q
            # TODO: Same as SCAN but only include fields starting with prefix.
            # See spec/level2.md
            raise NotImplementedError("SCAN_BY_PREFIX — see spec/level2.md")

        # ------------------------------------------------------------------ #
        # LEVEL 3 — TTL / expiration                                          #
        # ------------------------------------------------------------------ #

        elif op == "SET_WITH_TTL":
            # q is ["SET_WITH_TTL", ts, key, field, value, ttl]
            _, ts, key, field, value, ttl = q
            # TODO: Store value at (key, field) with expiry = int(ts) + int(ttl).
            # Overwrites any existing value and/or TTL at (key, field).
            # Returns "".
            # See spec/level3.md
            raise NotImplementedError("SET_WITH_TTL — see spec/level3.md")

        elif op == "UPDATE_TTL":
            # q is ["UPDATE_TTL", ts, key, field, ttl]
            _, ts, key, field, ttl = q
            # TODO: Re-anchor TTL: new expiry = int(ts) + int(ttl).
            # Return "true" if (key, field) exists and is not expired at ts.
            # Return "false" if missing or already expired.
            # Does NOT change the stored value.
            # See spec/level3.md
            raise NotImplementedError("UPDATE_TTL — see spec/level3.md")

        # ------------------------------------------------------------------ #
        # LEVEL 4 — Backup / Restore                                          #
        # ------------------------------------------------------------------ #

        elif op == "BACKUP":
            # q is ["BACKUP", ts]
            _, ts = q
            # TODO: Snapshot all non-expired entries.
            # For each entry: store remaining_ttl = expiry_ts - int(ts), or None if no TTL.
            # Store snapshot in backups[int(ts)].
            # Return the count of non-expired (key, field) pairs as a string.
            # See spec/level4.md
            raise NotImplementedError("BACKUP — see spec/level4.md")

        elif op == "RESTORE":
            # q is ["RESTORE", ts, backup_ts]
            _, ts, backup_ts = q
            # TODO: Replace current db state with snapshot at backup_ts.
            # Re-anchor TTL'd entries: new expiry = int(ts) + remaining_ttl.
            # If no snapshot at backup_ts, do nothing.
            # Returns "" in both cases.
            # See spec/level4.md
            raise NotImplementedError("RESTORE — see spec/level4.md")

        else:
            raise ValueError(f"Unknown op: {op}")

    return out
