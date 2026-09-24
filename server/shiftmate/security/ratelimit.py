"""In-process token-bucket rate limits (technical spec §9.7; valid because the site server runs one worker, A-15)."""

from __future__ import annotations

import math
import threading
import time

from shiftmate.errors import ShiftMateException


class RateLimiter:
    def __init__(self, per_minute: int):
        self.capacity = float(per_minute)
        self.rate = per_minute / 60.0
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (self.capacity, now))
            tokens = min(self.capacity, tokens + (now - last) * self.rate)
            if tokens < 1.0:
                retry = math.ceil((1.0 - tokens) / self.rate)
                self._buckets[key] = (tokens, now)
                raise ShiftMateException(status_code=429, code="rate_limited",
                                         message=f"Too many requests. Retry in {retry} s.",
                                         headers={"Retry-After": str(retry)})
            self._buckets[key] = (tokens - 1.0, now)

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


login_per_user = RateLimiter(5)       # per (IP, username)
login_per_ip = RateLimiter(20)        # per IP
pairing_per_ip = RateLimiter(10)      # per IP
