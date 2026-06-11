from __future__ import annotations

import time
from dataclasses import dataclass, field

from fastapi import Request

from app.core.config import settings


@dataclass
class LoginAttemptState:
    attempts: list[float] = field(default_factory=list)
    locked_until: float = 0.0


class LoginRateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 15 * 60, lockout_seconds: int = 15 * 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._states: dict[str, LoginAttemptState] = {}

    def retry_after(self, key: str, now: float | None = None) -> int:
        now = now if now is not None else time.time()
        state = self._states.get(key)
        if not state or state.locked_until <= now:
            return 0
        return max(1, int(state.locked_until - now))

    def record_failure(self, key: str, now: float | None = None) -> int:
        now = now if now is not None else time.time()
        state = self._states.setdefault(key, LoginAttemptState())
        state.attempts = [ts for ts in state.attempts if now - ts <= self.window_seconds]
        state.attempts.append(now)
        if len(state.attempts) >= self.max_attempts:
            state.locked_until = now + self.lockout_seconds
            state.attempts.clear()
            return self.lockout_seconds
        return 0

    def record_success(self, key: str) -> None:
        self._states.pop(key, None)


login_rate_limiter = LoginRateLimiter()


def client_ip_from_request(request: Request) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
    return request.client.host if request.client else "unknown"


def login_rate_limit_key(request: Request, email: str) -> str:
    return f"{client_ip_from_request(request).lower()}:{email.strip().lower()}"
