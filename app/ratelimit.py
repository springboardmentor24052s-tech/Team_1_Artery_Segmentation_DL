"""Sliding-window rate limiter. In-memory and per process, which is enough for one API replica.
With several replicas, move the counters to Redis (the interface stays the same)."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, float]:
        """Record a hit for `key`. Returns (allowed, seconds_until_retry)."""
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > 10_000:  # keep memory bounded
                self._hits.clear()
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False, round(self.window - (now - q[0]), 1)
            q.append(now)
            return True, 0.0
