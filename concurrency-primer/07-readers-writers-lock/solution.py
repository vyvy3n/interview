"""
Exercise 07 — Readers-Writers Lock

Multiple concurrent readers are allowed; writers are exclusive.
No readers may be active during a write.

Allowed imports: threading (stdlib only)
"""

import threading


class RWLock:
    """
    Readers–writers lock using one threading.Condition.

    Why Condition (not just a Lock + if-check)?
    -------------------------------------------
    A plain Lock lets you update shared state atomically, but it does not give
    you a correct way to *sleep until* some other thread changes that state.
    Condition adds:
      - wait():  atomically release the Condition's lock and block until notify*
      - notify_all(): wake waiters so they re-check their predicate

    Every method uses ``with self._cond:`` so all reads/writes of the counters
    below happen under the same mutex — no torn reads or lost updates.
    """

    def __init__(self) -> None:
        # How many threads are inside read_acquire..read_release right now.
        self._reader_count = 0
        # True between write_acquire and write_release for exactly one writer.
        self._writer_active = False
        # Guards _reader_count / _writer_active and backs wait()/notify_all().
        self._cond = threading.Condition()

    def read_acquire(self) -> None:
        """Acquire the read lock.  Blocks if a writer is active."""
        # ``with self._cond`` acquires the Condition's underlying lock.
        with self._cond:
            # Predicate for entering read mode: no writer may be active.
            #
            # Why ``while``, not ``if``?
            # - Spurious wakeups are allowed: wait() can return even if nobody
            #   called notify — you must re-check the condition.
            # - Between your wakeup and your next line, another thread can flip
            #   the predicate (e.g. a writer slipped in). Re-check in a loop.
            while self._writer_active:
                # wait() releases the lock *while sleeping*, then re-acquires it
                # before returning. Other threads can now change state / notify.
                self._cond.wait()
            # We hold the lock and the predicate holds — record this reader.
            self._reader_count += 1

    def read_release(self) -> None:
        """Release the read lock.  The last reader notifies waiting writers."""
        with self._cond:
            self._reader_count -= 1
            # Writers block until _reader_count == 0. Only the *last* reader can
            # open that door; waking here lets blocked writers re-run their while.
            if self._reader_count == 0:
                # notify_all (not notify): many threads may wait on different
                # predicates (readers vs writers). Wake everyone; each re-checks
                # its own ``while`` and either proceeds or waits again.
                self._cond.notify_all()

    def write_acquire(self) -> None:
        """Acquire the write lock.  Blocks until all readers have released."""
        with self._cond:
            # Predicate for exclusive write mode:
            #   - no readers still in their read critical sections
            #   - no other writer already active (second writer must wait here)
            while self._reader_count > 0 or self._writer_active:
                self._cond.wait()
            self._writer_active = True

    def write_release(self) -> None:
        """Release the write lock and notify all waiting readers and writers."""
        with self._cond:
            self._writer_active = False
            # Readers were blocked on _writer_active; writers may wait on reader
            # count. Wake all waiters so each re-evaluates its while-condition.
            self._cond.notify_all()
