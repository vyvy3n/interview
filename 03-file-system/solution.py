"""
File System (mini Dropbox in memory).

You implement ONE function: solution(queries).

  - Input:  a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md first, then work level by level.

The skeleton below has the dispatch loop and variable unpacking pre-filled.
Fill in each branch body, remove the NotImplementedError, and run the tests.

Operations by level:
  Level 1: FILE_UPLOAD, FILE_GET, FILE_COPY
  Level 2: FILE_SEARCH
  Level 3: USER_REGISTER, USER_UPLOAD, USER_GET, USER_COPY, USER_SEARCH
  Level 4: COMPRESS_FILE, DECOMPRESS_FILE, USER_MERGE
"""


def solution(queries):
    # ---------------------------------------------------------------
    # State — set up your data structures here.
    # ---------------------------------------------------------------
    #
    # Suggested starting shape (expand as you reach higher levels):
    #
    #   files: dict[str, dict]
    #     files[name] = {
    #       "size":          int,       # current stored size
    #       "original_size": int|None,  # set when compressed; None otherwise
    #       "owner":         str,       # "admin" for FILE_UPLOAD files
    #     }
    #
    #   users: dict[str, dict]
    #     users[user_id] = {
    #       "capacity": int,
    #       "used":     int,
    #     }
    #
    # You are free to restructure this however you like.

    files = {}   # name (str) -> {"size": int, "original_size": int|None, "owner": str}
    users = {}   # user_id (str) -> {"capacity": int, "used": int}

    out = []

    for q in queries:
        op = q[0]

        # ---------------------------------------------------------------
        # Level 1
        # ---------------------------------------------------------------

        if op == "FILE_UPLOAD":
            # q = ["FILE_UPLOAD", timestamp, name, size]
            _, timestamp, name, size = q
            # TODO: return "true" if uploaded, "false" if name already exists.
            # Hint: files owned by FILE_UPLOAD are owned by "admin".
            raise NotImplementedError("FILE_UPLOAD — see spec/level1.md")

        elif op == "FILE_GET":
            # q = ["FILE_GET", timestamp, name]
            _, timestamp, name = q
            # TODO: return size as string if file exists, else "".
            raise NotImplementedError("FILE_GET — see spec/level1.md")

        elif op == "FILE_COPY":
            # q = ["FILE_COPY", timestamp, source, dest]
            _, timestamp, source, dest = q
            # TODO: copy source → dest (overwrite dest if it exists).
            # Return "true" on success, "" if source missing.
            # The copy is owned by "admin".
            raise NotImplementedError("FILE_COPY — see spec/level1.md")

        # ---------------------------------------------------------------
        # Level 2
        # ---------------------------------------------------------------

        elif op == "FILE_SEARCH":
            # q = ["FILE_SEARCH", timestamp, prefix]
            _, timestamp, prefix = q
            # TODO: return top-10 files whose name starts with prefix,
            # sorted by size DESC then name ASC, formatted as:
            #   "name1(size1), name2(size2), ..."
            # Return "" if no matches.
            raise NotImplementedError("FILE_SEARCH — see spec/level2.md")

        # ---------------------------------------------------------------
        # Level 3
        # ---------------------------------------------------------------

        elif op == "USER_REGISTER":
            # q = ["USER_REGISTER", timestamp, user_id, capacity]
            _, timestamp, user_id, capacity = q
            # TODO: register user with given capacity.
            # Return "true" if new, "false" if already exists.
            raise NotImplementedError("USER_REGISTER — see spec/level3.md")

        elif op == "USER_UPLOAD":
            # q = ["USER_UPLOAD", timestamp, user_id, name, size]
            _, timestamp, user_id, name, size = q
            # TODO: upload file for user. Return remaining capacity as string.
            # Return "" if: user missing, name conflict (ANY owner), or exceeds capacity.
            raise NotImplementedError("USER_UPLOAD — see spec/level3.md")

        elif op == "USER_GET":
            # q = ["USER_GET", timestamp, user_id, name]
            _, timestamp, user_id, name = q
            # TODO: return file size as string ONLY IF user owns the file.
            # Return "" if file missing or not owned by user_id.
            raise NotImplementedError("USER_GET — see spec/level3.md")

        elif op == "USER_COPY":
            # q = ["USER_COPY", timestamp, user_id, source, dest]
            _, timestamp, user_id, source, dest = q
            # TODO: copy source (must be owned by user) to dest.
            # If dest exists and owned by user_id, overwrite (free old size first).
            # If dest exists owned by someone else, return "".
            # Return remaining capacity, or "" on any failure.
            raise NotImplementedError("USER_COPY — see spec/level3.md")

        elif op == "USER_SEARCH":
            # q = ["USER_SEARCH", timestamp, user_id, prefix]
            _, timestamp, user_id, prefix = q
            # TODO: same as FILE_SEARCH but only files owned by user_id.
            # Return "" if user missing or no matches.
            raise NotImplementedError("USER_SEARCH — see spec/level3.md")

        # ---------------------------------------------------------------
        # Level 4
        # ---------------------------------------------------------------

        elif op == "COMPRESS_FILE":
            # q = ["COMPRESS_FILE", timestamp, user_id, name]
            _, timestamp, user_id, name = q
            # TODO: compress file (new size = original_size // 2).
            # Return new size as string. Remember original for decompression.
            # Return "" if: user missing, file missing/not owned, or already compressed.
            raise NotImplementedError("COMPRESS_FILE — see spec/level4.md")

        elif op == "DECOMPRESS_FILE":
            # q = ["DECOMPRESS_FILE", timestamp, user_id, name]
            _, timestamp, user_id, name = q
            # TODO: restore compressed file to original size.
            # delta = original_size - compressed_size must fit in remaining capacity.
            # Return user's remaining capacity, or "" on failure.
            raise NotImplementedError("DECOMPRESS_FILE — see spec/level4.md")

        elif op == "USER_MERGE":
            # q = ["USER_MERGE", timestamp, user_id_a, user_id_b]
            _, timestamp, user_id_a, user_id_b = q
            # TODO: merge user_b into user_a.
            # Transfer all of B's files to A. Cap_a += cap_b. Used_a += used_b.
            # Fail (return "") if: either missing, a==b, or any name conflict.
            # Merge must be atomic — no partial transfer on failure.
            # Delete user_b on success.
            raise NotImplementedError("USER_MERGE — see spec/level4.md")

        else:
            raise ValueError(f"Unknown operation: {op!r}")

    return out
