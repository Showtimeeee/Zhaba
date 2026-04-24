import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_per_minute):
        self.max_per_minute = max_per_minute
        self.client_requests = defaultdict(list)

    def is_allowed(self, client_id):
        now = time.time()
        self.client_requests[client_id] = [
            t for t in self.client_requests[client_id] if now - t < 60
        ]
        if len(self.client_requests[client_id]) >= self.max_per_minute:
            return False
        self.client_requests[client_id].append(now)
        return True

    def get_remaining(self, client_id):
        now = time.time()
        self.client_requests[client_id] = [
            t for t in self.client_requests[client_id] if now - t < 60
        ]
        return max(0, self.max_per_minute - len(self.client_requests[client_id]))