"""
Concurrent Task Scheduler
=========================
Implement the TaskScheduler class across 6 levels.

Level guide:
  L1: submit_task, get_status, complete_task           -> spec/level1.md
  L2: list_by_status, count_by_status                  -> spec/level2.md
  L3: submit_task_with_priority, get_next_task         -> spec/level3.md
  L4: set_dependencies, get_next_runnable              -> spec/level4.md
  L5: start_workers, stop_workers                      -> spec/level5.md
  L6: cancel_task, wait_for_completion                 -> spec/level6.md
"""

import threading
import time


class TaskScheduler:
    def __init__(self):
        # task dict: task_id -> {status, duration, priority, order, deps, event}
        self._tasks = {}
        self._submit_counter = 0   # monotonically increasing, used as tie-breaker
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._threads = []

    # ------------------------------------------------------------------ #
    # Internal helpers                                                      #
    # ------------------------------------------------------------------ #

    def _is_runnable(self, task_id):
        """Return True if task is pending and all its deps are completed.
        Caller must hold self._lock."""
        info = self._tasks[task_id]
        if info["status"] != "pending":
            return False
        for dep_id in info["deps"]:
            if self._tasks[dep_id]["status"] != "completed":
                return False
        return True

    def _has_cycle(self, task_id, proposed_deps):
        """Return True if setting task_id's deps to proposed_deps would create a cycle.
        Uses DFS: starting from each proposed dep, see if we can reach task_id.
        Caller must hold self._lock."""
        visited = set()

        def dfs(current):
            if current == task_id:
                return True
            if current in visited:
                return False
            visited.add(current)
            for dep in self._tasks[current]["deps"]:
                if dfs(dep):
                    return True
            return False

        for dep in proposed_deps:
            if dfs(dep):
                return True
        return False

    def _propagate_cancel(self, cancelled_id):
        """Recursively cancel any pending/running tasks that depend on cancelled_id.
        Caller must hold self._lock."""
        for tid, info in self._tasks.items():
            if cancelled_id in info["deps"]:
                if info["status"] in ("pending", "running"):
                    info["status"] = "cancelled"
                    info["event"].set()
                    self._propagate_cancel(tid)

    def _worker_loop(self):
        """Main loop for each worker thread."""
        while not self._stop_event.is_set():
            task_id = None
            duration = None

            with self._lock:
                # Find and atomically claim the next runnable task
                best = None
                for tid, info in self._tasks.items():
                    if self._is_runnable(tid):
                        if best is None:
                            best = tid
                        else:
                            bi = self._tasks[best]
                            # Same tiebreak as get_next_runnable
                            if (info["priority"] > bi["priority"] or
                                    (info["priority"] == bi["priority"] and
                                     len(info["deps"]) > len(bi["deps"])) or
                                    (info["priority"] == bi["priority"] and
                                     len(info["deps"]) == len(bi["deps"]) and
                                     info["order"] < bi["order"])):
                                best = tid

                if best is not None:
                    task_id = best
                    duration = self._tasks[task_id]["duration"]
                    self._tasks[task_id]["status"] = "running"

            if task_id is not None:
                # Sleep OUTSIDE the lock to allow concurrency
                time.sleep(duration)

                with self._lock:
                    # Only mark completed if not already cancelled
                    if self._tasks[task_id]["status"] == "running":
                        self._tasks[task_id]["status"] = "completed"
                        self._tasks[task_id]["event"].set()
                    # If status is "cancelled", event was already set by cancel_task
            else:
                # No runnable task found; yield briefly before retrying
                time.sleep(0.005)

    # ------------------------------------------------------------------ #
    # Level 1 — Submit & Complete                                          #
    # ------------------------------------------------------------------ #

    def submit_task(self, task_id: str, duration) -> bool:
        """Submit a new task with default priority 0. See spec/level1.md."""
        return self.submit_task_with_priority(task_id, duration, 0)

    def get_status(self, task_id: str) -> str:
        """Return current status of task, or '' if missing. See spec/level1.md."""
        with self._lock:
            if task_id not in self._tasks:
                return ""
            return self._tasks[task_id]["status"]

    def complete_task(self, task_id: str) -> bool:
        """Mark a pending task as completed. See spec/level1.md."""
        with self._lock:
            if task_id not in self._tasks:
                return False
            info = self._tasks[task_id]
            if info["status"] != "pending":
                return False
            info["status"] = "completed"
            info["event"].set()
            return True

    # ------------------------------------------------------------------ #
    # Level 2 — Status Reports                                             #
    # ------------------------------------------------------------------ #

    def list_by_status(self, status: str) -> list:
        """Return sorted list of task_ids with the given status. See spec/level2.md."""
        with self._lock:
            return sorted(
                tid for tid, info in self._tasks.items()
                if info["status"] == status
            )

    def count_by_status(self, status: str) -> int:
        """Return count of tasks with the given status. See spec/level2.md."""
        with self._lock:
            return sum(1 for info in self._tasks.values() if info["status"] == status)

    # ------------------------------------------------------------------ #
    # Level 3 — Priorities                                                 #
    # ------------------------------------------------------------------ #

    def submit_task_with_priority(self, task_id: str, duration, priority: int) -> bool:
        """Submit a task with an explicit priority. See spec/level3.md."""
        with self._lock:
            if task_id in self._tasks:
                return False
            self._tasks[task_id] = {
                "status": "pending",
                "duration": duration,
                "priority": priority,
                "order": self._submit_counter,
                "deps": set(),
                "event": threading.Event(),
            }
            self._submit_counter += 1
            return True

    def get_next_task(self) -> str:
        """Return task_id of highest-priority pending task (read-only). See spec/level3.md."""
        with self._lock:
            best = None
            for tid, info in self._tasks.items():
                if info["status"] != "pending":
                    continue
                if best is None:
                    best = tid
                else:
                    if (info["priority"] > self._tasks[best]["priority"] or
                            (info["priority"] == self._tasks[best]["priority"] and
                             info["order"] < self._tasks[best]["order"])):
                        best = tid
            return best if best is not None else ""

    # ------------------------------------------------------------------ #
    # Level 4 — Dependencies                                               #
    # ------------------------------------------------------------------ #

    def set_dependencies(self, task_id: str, dep_ids: list) -> bool:
        """Set dependency list for task_id; returns False on cycle. See spec/level4.md."""
        with self._lock:
            # task_id must exist
            if task_id not in self._tasks:
                return False
            # All dep_ids must exist
            for dep in dep_ids:
                if dep not in self._tasks:
                    return False
            # Check for cycles: with the proposed deps set, would there be a cycle?
            proposed = set(dep_ids)
            if self._has_cycle(task_id, proposed):
                return False
            # Apply
            self._tasks[task_id]["deps"] = proposed
            return True

    def get_next_runnable(self) -> str:
        """Return highest-priority pending task whose deps are all completed. See spec/level4.md."""
        with self._lock:
            best = None
            for tid, info in self._tasks.items():
                if not self._is_runnable(tid):
                    continue
                if best is None:
                    best = tid
                else:
                    bi = self._tasks[best]
                    # Tiebreak order: priority desc, dep-count desc, submission order asc
                    if (info["priority"] > bi["priority"] or
                            (info["priority"] == bi["priority"] and
                             len(info["deps"]) > len(bi["deps"])) or
                            (info["priority"] == bi["priority"] and
                             len(info["deps"]) == len(bi["deps"]) and
                             info["order"] < bi["order"])):
                        best = tid
            return best if best is not None else ""

    # ------------------------------------------------------------------ #
    # Level 5 — Concurrent Workers                                         #
    # ------------------------------------------------------------------ #

    def start_workers(self, count: int) -> None:
        """Spawn count worker threads that auto-process runnable tasks. See spec/level5.md."""
        for _ in range(count):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._threads.append(t)

    def stop_workers(self) -> None:
        """Signal workers to stop and join all threads. See spec/level5.md."""
        self._stop_event.set()
        for t in self._threads:
            t.join()
        self._threads.clear()
        self._stop_event.clear()

    # ------------------------------------------------------------------ #
    # Level 6 — Cancellation & Waiting                                     #
    # ------------------------------------------------------------------ #

    def cancel_task(self, task_id: str) -> bool:
        """Cancel task and propagate to dependents. See spec/level6.md."""
        with self._lock:
            if task_id not in self._tasks:
                return False
            info = self._tasks[task_id]
            if info["status"] not in ("pending", "running"):
                return False
            info["status"] = "cancelled"
            info["event"].set()
            self._propagate_cancel(task_id)
            return True

    def wait_for_completion(self, task_id: str, timeout: float = None) -> str:
        """Block until task is terminal; return final status or '' on timeout. See spec/level6.md."""
        with self._lock:
            if task_id not in self._tasks:
                return ""
            info = self._tasks[task_id]
            status = info["status"]
            if status in ("completed", "cancelled"):
                return status
            event = info["event"]

        # Release lock while waiting to avoid deadlock with workers
        event.wait(timeout=timeout)

        with self._lock:
            if task_id not in self._tasks:
                return ""
            status = self._tasks[task_id]["status"]
            if status in ("completed", "cancelled"):
                return status
            return ""
