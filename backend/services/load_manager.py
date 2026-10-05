# backend/services/load_manager.py
"""Admission control for neural-network work.

The NN is the only expensive thing this app does: ~4s of CPU per submission on a 4-core box,
and it saturates those cores. Two problems follow if requests are just let through:

1. Gunicorn has a fixed thread pool. If every thread is busy running the NN, cheap requests
   (loading a task list, a dashboard, a page) queue behind them and the whole app feels dead.
   So NN work gets its own, smaller budget and leaves threads spare for everything else.
2. Measured earlier in load testing: throughput is flat past ~4 concurrent analyses because the
   cores are already full - extra concurrency only adds contention and latency. Queueing is
   strictly better than admitting everything.

So: a bounded number of analyses run at once, the rest wait in an orderly queue, and if the
queue is so deep that waiting is pointless the request is refused with a 503 and a Retry-After
instead of leaving a student staring at a spinner for twenty minutes.
"""
import os
import threading
import time
from contextlib import contextmanager

# How many analyses may run at once. Keep it below gunicorn's thread count so light requests
# always have threads available.
MAX_CONCURRENT = max(1, int(os.environ.get('MAX_CONCURRENT_ANALYSES', '3')))

# How many may be waiting before we start refusing. This has to stay BELOW gunicorn's thread
# count (72, see gunicorn.conf.py): a waiting request is still holding its thread, so a queue
# limit above the thread count can never be reached - the thread pool would fill up first and
# then even a dashboard page load would hang, which is the exact failure this module exists to
# prevent. 60 waiting + 3 running against 72 threads leaves ~9 threads always free for cheap
# requests. 60 was chosen from measurement, not taste: at 80 simultaneous submissions memory
# stayed near 4 GB of 8 GB and nothing failed except our own queue limit, so the limit is
# set by how long a wait is still worth having. 60 deep / 3 at a time x ~4s of work = ~80s in
# the worst case, which is a wait; past that it becomes a dead page, so we refuse instead.
MAX_QUEUED = max(1, int(os.environ.get('MAX_QUEUED_ANALYSES', '60')))

# Give up waiting after this long and refuse, rather than holding the connection forever.
QUEUE_TIMEOUT = float(os.environ.get('ANALYSIS_QUEUE_TIMEOUT', '600'))

# Used for wait estimates until we've measured real work on this box.
_DEFAULT_WORK_SECONDS = 4.0


class AtCapacity(Exception):
    """Raised when a request should be refused rather than queued."""

    def __init__(self, message, retry_after, snapshot):
        super().__init__(message)
        self.message = message
        self.retry_after = int(max(5, retry_after))
        self.snapshot = snapshot


class LoadManager:
    def __init__(self):
        self._semaphore = threading.BoundedSemaphore(MAX_CONCURRENT)
        # Reentrant: snapshot() builds its dict while holding the lock and calls helpers that
        # also want it. With a plain Lock that self-deadlocked - and because the deadlocked
        # thread never released it, every subsequent analysis blocked behind it too.
        self._lock = threading.RLock()
        self.in_flight = 0
        self.queued = 0
        self.peak_in_flight = 0
        self.peak_queued = 0
        self.completed = 0
        self.refused = 0
        self.timed_out = 0
        self._work_seconds_total = 0.0
        self._work_samples = 0
        self._wait_seconds_total = 0.0
        # Completions per call site ('submission', 'practice', 'analysis'), so the load endpoint
        # can say WHERE the load is coming from and not just how much of it there is.
        self._completed_by = {}

    # ---- observation ----

    @property
    def avg_work_seconds(self):
        if self._work_samples == 0:
            return _DEFAULT_WORK_SECONDS
        return self._work_seconds_total / self._work_samples

    def snapshot(self):
        with self._lock:
            return {
                'in_flight': self.in_flight,
                'queued': self.queued,
                'capacity': MAX_CONCURRENT,
                'queue_limit': MAX_QUEUED,
                'peak_in_flight': self.peak_in_flight,
                'peak_queued': self.peak_queued,
                'completed': self.completed,
                'completed_by': dict(self._completed_by),
                'refused': self.refused,
                'timed_out': self.timed_out,
                'avg_work_seconds': round(self.avg_work_seconds, 2),
                'avg_wait_seconds': round(
                    self._wait_seconds_total / self.completed, 2) if self.completed else 0.0,
                'estimated_wait_seconds': round(self.estimated_wait_unlocked(), 1),
                'saturated': self.in_flight >= MAX_CONCURRENT,
            }

    # ---- admission ----

    @contextmanager
    def slot(self, label='analysis'):
        """Occupy one analysis slot, queueing if necessary.

        Raises AtCapacity if the queue is already too deep, or if the wait exceeds
        QUEUE_TIMEOUT. Yields the number of seconds spent waiting.
        """
        with self._lock:
            if self.queued >= MAX_QUEUED:
                self.refused += 1
                snap = self.snapshot_unlocked()
                wait = self.estimated_wait_unlocked()
                raise AtCapacity(
                    "The server is busy analysing other students' work right now. "
                    "Please try again in a few minutes - nothing has been lost.",
                    retry_after=wait, snapshot=snap)
            self.queued += 1
            if self.queued > self.peak_queued:
                self.peak_queued = self.queued

        started_waiting = time.time()
        acquired = self._semaphore.acquire(timeout=QUEUE_TIMEOUT)
        waited = time.time() - started_waiting

        with self._lock:
            self.queued -= 1
            if not acquired:
                self.timed_out += 1
                self.refused += 1
                snap = self.snapshot_unlocked()
        if not acquired:
            raise AtCapacity(
                "The server is still busy after a long wait. Please try again shortly - "
                "nothing has been lost.",
                retry_after=60, snapshot=snap)

        with self._lock:
            self.in_flight += 1
            if self.in_flight > self.peak_in_flight:
                self.peak_in_flight = self.in_flight
            self._wait_seconds_total += waited

        work_started = time.time()
        try:
            yield waited
        finally:
            elapsed = time.time() - work_started
            self._semaphore.release()
            with self._lock:
                self.in_flight -= 1
                self.completed += 1
                self._completed_by[label] = self._completed_by.get(label, 0) + 1
                self._work_seconds_total += elapsed
                self._work_samples += 1

    # ---- internals (callers already hold the lock) ----

    def snapshot_unlocked(self):
        return {
            'in_flight': self.in_flight,
            'queued': self.queued,
            'capacity': MAX_CONCURRENT,
            'queue_limit': MAX_QUEUED,
        }

    def estimated_wait_unlocked(self):
        """Roughly how long a request joining the queue now would wait: every slot clears one
        job per avg_work_seconds, so the backlog divided by the slot count is the wait."""
        return ((self.queued + self.in_flight) / MAX_CONCURRENT) * self.avg_work_seconds


# One shared instance per worker process. Note this is per-process state: with the single
# gunicorn worker this app runs (see gunicorn.conf.py) that is the whole picture. If workers
# are ever increased, each gets its own budget, so divide MAX_CONCURRENT accordingly.
manager = LoadManager()
