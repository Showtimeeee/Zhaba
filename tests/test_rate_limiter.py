import pytest
import time
from src.core import RateLimiter


class TestRateLimiter:
    def test_allowed_under_limit(self):
        limiter = RateLimiter(max_per_minute=5)
        assert limiter.is_allowed("client1") is True
        assert limiter.get_remaining("client1") == 4

    def test_blocked_over_limit(self):
        limiter = RateLimiter(max_per_minute=2)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.is_allowed("client1") is False

    def test_different_clients(self):
        limiter = RateLimiter(max_per_minute=1)
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client2") is True

    def test_remaining_calculation(self):
        limiter = RateLimiter(max_per_minute=5)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.get_remaining("client1") == 3