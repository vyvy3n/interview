"""
Bank Transaction System.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

The skeleton below has the loop set up for you. You fill in the branch
bodies for each level. Delete the NotImplementedError once you start.

Level 1: CREATE_ACCOUNT, DEPOSIT, PAY           — see spec/level1.md
Level 2: TRANSFER, TOP_SPENDERS                 — see spec/level2.md
Level 3: SCHEDULE_PAYMENT, CANCEL_PAYMENT       — see spec/level3.md
Level 4: MERGE_ACCOUNTS                         — see spec/level4.md
"""


def solution(queries):
    accounts = {}   # account_id (str) -> balance (int)
    out = []

    for q in queries:
        op = q[0]

        if op == "CREATE_ACCOUNT":
            # q is ["CREATE_ACCOUNT", timestamp, account_id]
            _, timestamp, account_id = q
            # TODO: append "true" if newly created, "false" if already exists.
            if account_id in accounts:
                out.append("false")
            else:
                accounts[account_id] = 0
                out.append("true")

        elif op == "DEPOSIT":
            # q is ["DEPOSIT", timestamp, account_id, amount]
            _, timestamp, account_id, amount = q
            # TODO: append new balance as a string, or "" if account missing.
            if account_id not in accounts:
                out.append("")
            else:
                accounts[account_id] += int(amount)
                out.append(str(accounts[account_id]))

        elif op == "PAY":
            # q is ["PAY", timestamp, account_id, amount]
            _, timestamp, account_id, amount = q
            # TODO: append new balance as string, or "" if missing/insufficient.
            #       Do NOT deduct on insufficient funds.
            if account_id not in accounts:
                out.append("")
            else:
                if accounts[account_id] >= int(amount):
                    accounts[account_id] -= int(amount)
                    out.append(str(accounts[account_id]))
                else:
                    out.append("")

        # --- Level 2 ---

        elif op == "TRANSFER":
            # q is ["TRANSFER", timestamp, from_id, to_id, amount]
            _, timestamp, from_id, to_id, amount = q
            # TODO: Move amount from from_id to to_id atomically.
            #       Return new balance of from_id as string.
            #       Return "" if either account missing, from_id==to_id, or insufficient funds.
            #       Count amount toward from_id's outgoing total on success.
            raise NotImplementedError("TRANSFER — see spec/level2.md")

        elif op == "TOP_SPENDERS":
            # q is ["TOP_SPENDERS", timestamp, n]
            _, timestamp, n = q
            # TODO: Return top-n accounts by total outgoing (PAY + TRANSFER amounts sent).
            #       Format: "alice(500), bob(300), carol(200)"
            #       Sort: outgoing DESC, ties broken by account_id ASC (alphabetical).
            #       If fewer than n accounts exist, return all of them.
            raise NotImplementedError("TOP_SPENDERS — see spec/level2.md")

        # --- Level 3 ---

        elif op == "SCHEDULE_PAYMENT":
            # q is ["SCHEDULE_PAYMENT", timestamp, account_id, amount, delay]
            _, timestamp, account_id, amount, delay = q
            # TODO: Before processing, fire any pending payments with execute_time <= int(timestamp).
            #       Register a future payment firing at int(timestamp) + int(delay).
            #       Return global sequential payment_id (e.g. "payment1") if account exists.
            #       Return "" if account does not exist (do NOT increment counter).
            raise NotImplementedError("SCHEDULE_PAYMENT — see spec/level3.md")

        elif op == "CANCEL_PAYMENT":
            # q is ["CANCEL_PAYMENT", timestamp, account_id, payment_id]
            _, timestamp, account_id, payment_id = q
            # TODO: Before processing, fire any pending payments with execute_time <= int(timestamp).
            #       Return "true" if payment exists, belongs to account_id, and hasn't fired/been cancelled.
            #       Return "" otherwise (account missing, payment missing, wrong owner, already fired).
            raise NotImplementedError("CANCEL_PAYMENT — see spec/level3.md")

        # --- Level 4 ---

        elif op == "MERGE_ACCOUNTS":
            # q is ["MERGE_ACCOUNTS", timestamp, id1, id2]
            _, timestamp, id1, id2 = q
            # TODO: Before processing, fire any pending payments with execute_time <= int(timestamp).
            #       Merge id2 into id1: combine balances, combine outgoing totals,
            #       reassign all pending (unfired, uncancelled) payments from id2 to id1.
            #       Delete id2 entirely. Return "true" on success.
            #       Return "" if either account missing or id1 == id2.
            raise NotImplementedError("MERGE_ACCOUNTS — see spec/level4.md")

        else:
            raise ValueError(f"Unknown op: {op}")

    return out
