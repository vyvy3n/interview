"""
Bank Account System
===================
Implement the Bank class across 6 levels.

Level guide:
  L1: open_account, get_balance, deposit, withdraw                    -> spec/level1.md
  L2: transfer, get_transaction_history                               -> spec/level2.md
  L3: schedule_transfer, cancel_scheduled, tick                       -> spec/level3.md
  L4: apply_interest, merge_accounts                                  -> spec/level4.md
  L5: thread-safe + start_scheduler, stop_scheduler, advance_time    -> spec/level5.md
  L6: compare_and_deposit, batch_transfer, wait_for_balance          -> spec/level6.md
"""

import threading
import time


class Bank:
    def __init__(self):
        # accounts: account_id -> {"balance": int, "history": list[str]}
        self._accounts = {}

        # scheduled transfers: sched_id -> {"from_id", "to_id", "amount", "execute_at", "cancelled"}
        self._scheduled = {}
        self._sched_counter = 0  # global counter for sched_1, sched_2, ...

        # internal clock for the background scheduler
        self._clock = 0

        # threading
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._scheduler_thread = None

        # L6: condition variable for wait_for_balance
        self._balance_condition = threading.Condition(self._lock)

    # ------------------------------------------------------------------ #
    # Level 1 — Account Lifecycle                                          #
    # ------------------------------------------------------------------ #

    def open_account(self, account_id: str) -> bool:
        """Open a new account with balance 0. Returns True if opened, False if exists."""
        with self._lock:
            if account_id in self._accounts:
                return False
            self._accounts[account_id] = {"balance": 0, "history": []}
            return True

    def get_balance(self, account_id: str) -> int:
        """Return current balance, or -1 if account missing."""
        with self._lock:
            if account_id not in self._accounts:
                return -1
            return self._accounts[account_id]["balance"]

    def deposit(self, account_id: str, amount: int) -> int:
        """Deposit amount into account. Returns new balance, or -1 if missing."""
        with self._lock:
            if account_id not in self._accounts:
                return -1
            acct = self._accounts[account_id]
            acct["balance"] += amount
            acct["history"].insert(0, f"deposit:{amount}")
            # Notify waiters (L6)
            self._balance_condition.notify_all()
            return acct["balance"]

    def withdraw(self, account_id: str, amount: int) -> int:
        """Withdraw amount. Returns new balance, or -1 if missing or insufficient funds."""
        with self._lock:
            if account_id not in self._accounts:
                return -1
            acct = self._accounts[account_id]
            if acct["balance"] < amount:
                return -1
            acct["balance"] -= amount
            acct["history"].insert(0, f"withdraw:{amount}")
            return acct["balance"]

    # ------------------------------------------------------------------ #
    # Level 2 — Transfers + History                                        #
    # ------------------------------------------------------------------ #

    def transfer(self, from_id: str, to_id: str, amount: int) -> int:
        """Transfer amount from from_id to to_id.
        Returns new balance of from_id, or -1 on any failure."""
        with self._lock:
            # Validate
            if from_id not in self._accounts:
                return -1
            if to_id not in self._accounts:
                return -1
            if from_id == to_id:
                return -1
            from_acct = self._accounts[from_id]
            to_acct = self._accounts[to_id]
            if from_acct["balance"] < amount:
                return -1
            # Execute
            from_acct["balance"] -= amount
            to_acct["balance"] += amount
            from_acct["history"].insert(0, f"transfer_out:{amount}:to_{to_id}")
            to_acct["history"].insert(0, f"transfer_in:{amount}:from_{from_id}")
            # Notify waiters (L6)
            self._balance_condition.notify_all()
            return from_acct["balance"]

    def get_transaction_history(self, account_id: str, n: int) -> list:
        """Return last n transactions for account_id, newest first.
        Returns [] if account missing or no history."""
        with self._lock:
            if account_id not in self._accounts:
                return []
            history = self._accounts[account_id]["history"]
            return history[:n]

    # ------------------------------------------------------------------ #
    # Level 3 — Scheduled Transfers                                        #
    # ------------------------------------------------------------------ #

    def schedule_transfer(self, from_id: str, to_id: str, amount: int, execute_at: int) -> str:
        """Schedule a transfer. Returns scheduled_id or '' on validation failure."""
        with self._lock:
            if from_id not in self._accounts:
                return ""
            if to_id not in self._accounts:
                return ""
            if from_id == to_id:
                return ""
            self._sched_counter += 1
            sched_id = f"sched_{self._sched_counter}"
            self._scheduled[sched_id] = {
                "from_id": from_id,
                "to_id": to_id,
                "amount": amount,
                "execute_at": execute_at,
                "cancelled": False,
                "executed": False,
            }
            return sched_id

    def cancel_scheduled(self, scheduled_id: str) -> bool:
        """Cancel a scheduled transfer. Returns True if cancelled, False otherwise."""
        with self._lock:
            if scheduled_id not in self._scheduled:
                return False
            sched = self._scheduled[scheduled_id]
            if sched["cancelled"] or sched["executed"]:
                return False
            sched["cancelled"] = True
            return True

    def tick(self, now: int) -> int:
        """Advance time to now. Execute due scheduled transfers in creation order.
        Returns count of successfully executed transfers."""
        with self._lock:
            # Collect pending scheduled ids that are due, in sched_id order
            due = sorted(
                (sid for sid, s in self._scheduled.items()
                 if not s["cancelled"] and not s["executed"] and s["execute_at"] <= now),
                key=lambda sid: int(sid.split("_")[1])
            )
            executed = 0
            for sid in due:
                sched = self._scheduled[sid]
                from_id = sched["from_id"]
                to_id = sched["to_id"]
                amount = sched["amount"]
                # Check validity at execution time
                if from_id not in self._accounts:
                    sched["executed"] = True  # skip but mark done
                    continue
                if to_id not in self._accounts:
                    sched["executed"] = True
                    continue
                from_acct = self._accounts[from_id]
                to_acct = self._accounts[to_id]
                if from_acct["balance"] < amount:
                    sched["executed"] = True
                    continue
                # Execute
                from_acct["balance"] -= amount
                to_acct["balance"] += amount
                from_acct["history"].insert(0, f"transfer_out:{amount}:to_{to_id}")
                to_acct["history"].insert(0, f"transfer_in:{amount}:from_{from_id}")
                sched["executed"] = True
                executed += 1
            # Notify waiters (L6)
            if executed > 0:
                self._balance_condition.notify_all()
            return executed

    # ------------------------------------------------------------------ #
    # Level 4 — Interest + Merge                                           #
    # ------------------------------------------------------------------ #

    def apply_interest(self, rate_basis_points: int) -> dict:
        """Apply interest to all accounts. Returns {account_id: new_balance} sorted alphabetically."""
        with self._lock:
            result = {}
            for account_id in sorted(self._accounts.keys()):
                acct = self._accounts[account_id]
                interest = acct["balance"] * rate_basis_points // 10000
                acct["balance"] += interest
                result[account_id] = acct["balance"]
            # Notify waiters if any balances changed
            self._balance_condition.notify_all()
            return result

    def merge_accounts(self, survivor_id: str, absorbed_id: str) -> bool:
        """Merge absorbed_id into survivor_id. Returns False if either missing or same id."""
        with self._lock:
            if survivor_id not in self._accounts:
                return False
            if absorbed_id not in self._accounts:
                return False
            if survivor_id == absorbed_id:
                return False
            survivor = self._accounts[survivor_id]
            absorbed = self._accounts[absorbed_id]
            # Combine balances
            survivor["balance"] += absorbed["balance"]
            # Survivor's recent events are still most recent, so they stay at the front.
            # Absorbed history is appended after (it's "older" from the survivor's perspective).
            survivor["history"] = survivor["history"] + absorbed["history"]
            # Re-anchor pending scheduled transfers
            for sched in self._scheduled.values():
                if sched["cancelled"] or sched["executed"]:
                    continue
                if sched["from_id"] == absorbed_id:
                    sched["from_id"] = survivor_id
                if sched["to_id"] == absorbed_id:
                    sched["to_id"] = survivor_id
            # Remove absorbed account
            del self._accounts[absorbed_id]
            # Notify waiters
            self._balance_condition.notify_all()
            return True

    # ------------------------------------------------------------------ #
    # Level 5 — Concurrent Operations (Threading)                          #
    # ------------------------------------------------------------------ #

    def advance_time(self, amount: int) -> int:
        """Advance the bank's internal clock by amount and execute due transfers.
        Returns count of successfully executed transfers."""
        with self._lock:
            self._clock += amount
            return self.tick(self._clock)

    def start_scheduler(self, check_interval: float = 0.05) -> None:
        """Start a background thread that periodically advances time.
        Only one scheduler thread is allowed at a time."""
        with self._lock:
            if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
                return  # already running

        self._stop_event.clear()

        def _scheduler_loop():
            while not self._stop_event.is_set():
                self.advance_time(1)
                time.sleep(check_interval)

        self._scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop_scheduler(self) -> None:
        """Signal the background scheduler thread to stop and join it."""
        self._stop_event.set()
        if self._scheduler_thread is not None:
            self._scheduler_thread.join()
            self._scheduler_thread = None

    # ------------------------------------------------------------------ #
    # Level 6 — Atomic Compound Operations                                 #
    # ------------------------------------------------------------------ #

    def compare_and_deposit(self, account_id: str, expected_balance: int, deposit_amount: int) -> bool:
        """Atomically: if balance == expected_balance, deposit and return True; else False.
        Account must exist."""
        with self._lock:
            if account_id not in self._accounts:
                return False
            acct = self._accounts[account_id]
            if acct["balance"] != expected_balance:
                return False
            acct["balance"] += deposit_amount
            acct["history"].insert(0, f"deposit:{deposit_amount}")
            self._balance_condition.notify_all()
            return True

    def batch_transfer(self, transfers: list) -> bool:
        """Atomically execute a list of (from_id, to_id, amount) transfers.
        ALL must succeed or NONE. Returns False if any check fails."""
        with self._lock:
            # Validate all transfers upfront against start state
            # We need to check balances considering all the transfers together (per-account tracking)
            balance_deltas = {}  # account_id -> net delta

            for from_id, to_id, amount in transfers:
                if from_id not in self._accounts:
                    return False
                if to_id not in self._accounts:
                    return False
                if from_id == to_id:
                    return False
                balance_deltas[from_id] = balance_deltas.get(from_id, 0) - amount
                balance_deltas[to_id] = balance_deltas.get(to_id, 0) + amount

            # Check that no account goes negative (based on start balance + deltas up to each withdrawal)
            # The spec says "every from_id must have sufficient funds at the START state"
            # So we check each from_id independently against its current balance
            # but we must also account for multiple withdrawals from the same account
            # "at the START state" means we check the sum of all withdrawals from each account
            from_totals = {}  # from_id -> total amount being withdrawn
            for from_id, to_id, amount in transfers:
                from_totals[from_id] = from_totals.get(from_id, 0) + amount

            for from_id, total in from_totals.items():
                if self._accounts[from_id]["balance"] < total:
                    return False

            # All checks passed — execute all transfers
            for from_id, to_id, amount in transfers:
                from_acct = self._accounts[from_id]
                to_acct = self._accounts[to_id]
                from_acct["balance"] -= amount
                to_acct["balance"] += amount
                from_acct["history"].insert(0, f"transfer_out:{amount}:to_{to_id}")
                to_acct["history"].insert(0, f"transfer_in:{amount}:from_{from_id}")

            self._balance_condition.notify_all()
            return True

    def wait_for_balance(self, account_id: str, target_balance: int, timeout: float = None) -> bool:
        """Block until account's balance >= target_balance (or timeout).
        Returns True if reached, False on timeout or missing account."""
        with self._lock:
            if account_id not in self._accounts:
                return False
            # Check immediately
            if self._accounts[account_id]["balance"] >= target_balance:
                return True

            # Wait using the condition variable
            deadline = None
            if timeout is not None:
                deadline = time.monotonic() + timeout

            while True:
                if account_id not in self._accounts:
                    return False
                if self._accounts[account_id]["balance"] >= target_balance:
                    return True

                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    self._balance_condition.wait(timeout=remaining)
                else:
                    self._balance_condition.wait()
