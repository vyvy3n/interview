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


class File: 
    def __init__(self, name, size, owner):
        self.name = name
        self.size = size
        self.owner = owner        


class User:
    def __init__(self, user_id, capacity):
        self.user_id = user_id
        self.capacity = capacity
        self.used = 0


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

    files = {}   # name (str) -> File() object
    users = {}   # user_id (str) -> User() object

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
            if name in files.keys():
                out.append("false")
            else:
                files[name] = File(name, size, "admin")
                out.append("true")

        elif op == "FILE_GET":
            # q = ["FILE_GET", timestamp, name]
            _, timestamp, name = q
            # TODO: return size as string if file exists, else "".
            if name in files.keys():
                out.append(str(files[name].size))
            else:
                out.append("")

        elif op == "FILE_COPY":
            # q = ["FILE_COPY", timestamp, source, dest]
            _, timestamp, source, dest = q
            # TODO: copy source → dest (overwrite dest if it exists).
            # Return "true" on success, "" if source missing.
            # The copy is owned by "admin".
            if source in files.keys():
                if dest in files.keys():  # overwrite dest if it exists
                    files[dest] = File(dest, files[source].size, "admin")
                    out.append("true")
                else:
                    files[dest] = File(dest, files[source].size, "admin")
                    out.append("true")
            else:
                out.append("")

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
            matches = [f for f in files.values() if f.name.startswith(prefix)]
            matches.sort(key=lambda f: (-int(f.size), f.name))
            top = matches[:10]
            if not top:
                out.append("")
            else:
                out.append(", ".join(f"{f.name}({f.size})" for f in top))

        # ---------------------------------------------------------------
        # Level 3
        # ---------------------------------------------------------------

        elif op == "USER_REGISTER":
            # q = ["USER_REGISTER", timestamp, user_id, capacity]
            _, timestamp, user_id, capacity = q
            # TODO: register user with given capacity.
            # Return "true" if new, "false" if already exists.
            if user_id in users.keys():
                out.append("false")
            else:
                users[user_id] = User(user_id, int(capacity))
                out.append("true")

        elif op == "USER_UPLOAD":
            # q = ["USER_UPLOAD", timestamp, user_id, name, size]
            _, timestamp, user_id, name, size = q
            # TODO: upload file for user. Return remaining capacity as string.
            # Return "" if: user missing, name conflict (ANY owner), or exceeds capacity.
            if user_id not in users.keys():
                out.append("")
            elif name in files.keys():
                out.append("")
            elif users[user_id].used + int(size) > users[user_id].capacity:
                out.append("")
            else:
                sz = int(size)
                files[name] = File(name, sz, user_id)
                u = users[user_id]
                u.used += sz
                out.append(str(u.capacity - u.used))

        elif op == "USER_GET":
            # q = ["USER_GET", timestamp, user_id, name]
            _, timestamp, user_id, name = q
            # TODO: return file size as string ONLY IF user owns the file.
            # Return "" if file missing or not owned by user_id.
            if name in files.keys() and files[name].owner == user_id:
                out.append(str(files[name].size))
            else:
                out.append("")

        elif op == "USER_COPY":
            # q = ["USER_COPY", timestamp, user_id, source, dest]
            _, timestamp, user_id, source, dest = q
            # TODO: copy source (must be owned by user) to dest.
            # If dest exists and owned by user_id, overwrite (free old size first).
            # If dest exists owned by someone else, return "".
            # Return remaining capacity, or "" on any failure.
            if source in files.keys() and files[source].owner == user_id:
                if dest in files.keys():
                    if files[dest].owner == user_id:
                        if (files[source].size - files[dest].size) <= (users[user_id].capacity - users[user_id].used):
                            users[user_id].used -= files[dest].size
                            users[user_id].used += files[source].size
                            out.append(str(users[user_id].capacity - users[user_id].used))
                            files[dest] = File(dest, files[source].size, user_id)
                        else:
                            out.append("")
                    else:
                        out.append("")
                else:       
                    if (files[source].size) <= (users[user_id].capacity - users[user_id].used):
                        files[dest] = File(dest, files[source].size, user_id)
                        users[user_id].used += files[source].size
                        out.append(str(users[user_id].capacity - users[user_id].used))
                    else:
                        out.append("")
            else:  # source not exists or not owned by user_id
                out.append("")

        elif op == "USER_SEARCH":
            # q = ["USER_SEARCH", timestamp, user_id, prefix]
            _, timestamp, user_id, prefix = q
            # TODO: same as FILE_SEARCH but only files owned by user_id.
            # Return "" if user missing or no matches.
            if user_id not in users.keys():
                out.append("")
            else:
                matches = [f for f in files.values() if f.owner == user_id and f.name.startswith(prefix)]
                matches.sort(key=lambda f: (-int(f.size), f.name))
                top = matches[:10]
                if not top:
                    out.append("")
                else:
                    out.append(", ".join(f"{f.name}({f.size})" for f in top))
        # ---------------------------------------------------------------
        # Level 4
        # ---------------------------------------------------------------

        elif op == "COMPRESS_FILE":
            # q = ["COMPRESS_FILE", timestamp, user_id, name]
            _, timestamp, user_id, name = q
            # TODO: compress file (new size = original_size // 2).
            # Return new size as string. Remember original for decompression.
            # Return "" if: user missing, file missing/not owned, or already compressed.
            # if user_id not in users.keys():

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
