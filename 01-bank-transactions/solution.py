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


class Account:
    def __init__(self, account_id):
        self.account_id = account_id
        self.balance = 0
        self.outgoing = 0

    def deposit(self, amount):
        self.balance += int(amount)

    def pay(self, amount):
        self.balance -= int(amount)
        self.outgoing += int(amount)

    def transfer(self, amount):
        self.balance -= int(amount)
        self.outgoing += int(amount)

    def get_balance(self):
        return str(self.balance)

    def get_outgoing(self):
        return str(self.outgoing)


def solution(queries):
    accounts = {}  # account_id (str) -> Account(account_id)
    out = []
    payment_count = 0
    pending_payments = {}  # payment_id (str) -> Payment(payment_id)

    class Payment:
        def __init__(self, timestamp, account_id, amount, delay, payment_count):
            self.execute_time = int(timestamp) + int(delay)
            self.account_id = account_id
            self.amount = int(amount)
            self.fired = False
            self.payment_count = payment_count

        def fire(self):
            # fire only if account has enough balance
            if accounts[self.account_id].balance >= self.amount:
                accounts[self.account_id].balance -= self.amount
                accounts[self.account_id].outgoing += self.amount
            # skip if account has insufficient balance; but still mark as fired
            self.fired = True
    
    def fire_pending_payments(ts):
        to_be_fired_pid = []
        for pid, payment in pending_payments.items():
            if payment.execute_time <= int(ts):
                payment.fire()
                to_be_fired_pid.append(pid)
        
        for pid in to_be_fired_pid:
            pending_payments.pop(pid)

    for q in queries:
        op = q[0]
        ts = q[1]
        fire_pending_payments(ts)

        if op == "CREATE_ACCOUNT":
            # q is ["CREATE_ACCOUNT", timestamp, account_id]
            _, timestamp, account_id = q
            # TODO: append "true" if newly created, "false" if already exists.
            if account_id in accounts:
                out.append("false")
            else:
                account_instance = Account(account_id)  # create a new account instance
                accounts[account_id] = account_instance
                out.append("true")

        elif op == "DEPOSIT":
            # q is ["DEPOSIT", timestamp, account_id, amount]
            _, timestamp, account_id, amount = q
            # TODO: append new balance as a string, or "" if account missing.
            if account_id not in accounts:
                out.append("")
            else:
                accounts[account_id].deposit(amount)
                out.append(str(accounts[account_id].balance))

        elif op == "PAY":
            # q is ["PAY", timestamp, account_id, amount]
            _, timestamp, account_id, amount = q
            # TODO: append new balance as string, or "" if missing/insufficient.
            #       Do NOT deduct on insufficient funds.
            if account_id not in accounts:
                out.append("")
            else:
                if accounts[account_id].balance >= int(amount):
                    accounts[account_id].pay(amount)
                    out.append(str(accounts[account_id].balance))
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
            # raise NotImplementedError("TRANSFER — see spec/level2.md")
            if from_id not in accounts:
                out.append("")
            elif to_id not in accounts:
                out.append("")
            elif from_id == to_id:
                out.append("")
            elif accounts[from_id].balance < int(amount):
                out.append("")
            else:
                accounts[from_id].transfer(amount) 
                accounts[to_id].deposit(amount)
                out.append(str(accounts[from_id].balance))

        elif op == "TOP_SPENDERS":
            # q is ["TOP_SPENDERS", timestamp, n]
            _, timestamp, n = q
            # TODO: Return top-n accounts by total outgoing (PAY + TRANSFER amounts sent).
            #       Format: "alice(500), bob(300), carol(200)"
            #       Sort: outgoing DESC, ties broken by account_id ASC (alphabetical).
            #       If fewer than n accounts e xist, return all of them.
            if n == 0:
                return ""
            
            sorted_accounts = sorted(accounts.values(), key=lambda x: (-x.outgoing, x.account_id))
            top_n_accounts = sorted_accounts[:int(n)]
            out.append(", ".join([f"{account.account_id}({account.outgoing})" for account in top_n_accounts]))

        # --- Level 3 ---

        elif op == "SCHEDULE_PAYMENT":
            # q is ["SCHEDULE_PAYMENT", timestamp, account_id, amount, delay]
            _, timestamp, account_id, amount, delay = q
            # TODO: Before processing, fire any pending payments with execute_time <= int(timestamp).
            #       Register a future payment firing at int(timestamp) + int(delay).
            #       Return global sequential payment_id (e.g. "payment1") if account exists.
            #       Return "" if account does not exist (do NOT increment counter).

            # handle scheduling of payment
            if account_id in accounts:
                payment_count += 1
                payment_id = f"payment{payment_count}"
                pending_payments[payment_id] = Payment(timestamp, account_id, amount, delay, payment_count)
                out.append(payment_id)
            else:
                out.append("")

        elif op == "CANCEL_PAYMENT":
            # q is ["CANCEL_PAYMENT", timestamp, account_id, payment_id]
            _, timestamp, account_id, payment_id = q
            # TODO: Before processing, fire any pending payments with execute_time <= int(timestamp).
            #       Return "true" if payment exists, belongs to account_id, and hasn't fired/been cancelled.
            #       Return "" otherwise (account missing, payment missing, wrong owner, already fired).

            if payment_id in pending_payments:
                if pending_payments[payment_id].account_id == account_id:
                    if pending_payments[payment_id].fired == True:
                        out.append("")
                    else:
                        pending_payments.pop(payment_id)
                        out.append("true")
                else:
                    out.append("")
            else:
                out.append("")

        # --- Level 4 ---

        elif op == "MERGE_ACCOUNTS":
            # q is ["MERGE_ACCOUNTS", timestamp, id1, id2]
            _, timestamp, id1, id2 = q
            # TODO: Before processing, fire any pending payments with execute_time <= int(timestamp).
            #       Merge id2 into id1: combine balances, combine outgoing totals,
            #       reassign all pending (unfired, uncancelled) payments from id2 to id1.
            #       Delete id2 entirely. Return "true" on success.
            #       Return "" if either account missing or id1 == id2.

            if id1 not in accounts:
                out.append("")
            elif id2 not in accounts:
                out.append("")
            elif id1 == id2:
                out.append("")
            else:
                accounts[id1].balance += accounts[id2].balance
                accounts[id1].outgoing += accounts[id2].outgoing
                for pid, payment in pending_payments.items():
                    if payment.account_id == id2:
                        payment.account_id = id1
                        # pending_payments[pid] = payment
                accounts.pop(id2)
                out.append("true")

        else:
            raise ValueError(f"Unknown op: {op}")

    return out
