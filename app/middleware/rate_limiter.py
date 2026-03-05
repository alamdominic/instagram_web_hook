# app/middleware/rate_limiter.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
import time

META_IP_RANGES = ["173.252.", "31.13.", "69.63.", "66.220."]


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/webhook" and request.method == "POST":
            client_ip = request.client.host

            # Optional: allowlist Meta IPs — skip rate limiting for them
            if any(client_ip.startswith(prefix) for prefix in META_IP_RANGES):
                return await call_next(request)

            # Sliding window counter
            now = time.time()
            window_start = now - self.window_seconds
            self._buckets[client_ip] = [
                t for t in self._buckets[client_ip] if t > window_start
            ]

            if len(self._buckets[client_ip]) >= self.max_requests:
                return JSONResponse(
                    status_code=429, content={"detail": "Too many requests"}
                )

            self._buckets[client_ip].append(now)

        return await call_next(request)
