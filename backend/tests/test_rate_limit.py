import unittest

from app.core.rate_limit import LoginRateLimiter


class LoginRateLimiterTests(unittest.TestCase):
    def test_locks_after_configured_failures(self):
        limiter = LoginRateLimiter(max_attempts=3, window_seconds=60, lockout_seconds=120)
        key = "127.0.0.1:user@example.com"

        self.assertEqual(limiter.record_failure(key, now=1000), 0)
        self.assertEqual(limiter.record_failure(key, now=1010), 0)
        self.assertEqual(limiter.record_failure(key, now=1020), 120)
        self.assertEqual(limiter.retry_after(key, now=1030), 110)

    def test_success_clears_failures(self):
        limiter = LoginRateLimiter(max_attempts=3, window_seconds=60, lockout_seconds=120)
        key = "127.0.0.1:user@example.com"

        limiter.record_failure(key, now=1000)
        limiter.record_success(key)

        self.assertEqual(limiter.retry_after(key, now=1001), 0)
        self.assertEqual(limiter.record_failure(key, now=1002), 0)

    def test_old_failures_expire_outside_window(self):
        limiter = LoginRateLimiter(max_attempts=2, window_seconds=10, lockout_seconds=120)
        key = "127.0.0.1:user@example.com"

        limiter.record_failure(key, now=1000)
        self.assertEqual(limiter.record_failure(key, now=1011), 0)
        self.assertEqual(limiter.retry_after(key, now=1012), 0)


if __name__ == "__main__":
    unittest.main()
