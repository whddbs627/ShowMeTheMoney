"""
보안 미들웨어: Rate limiting, 에러 핸들링
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP 기반 rate limiting"""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 테스트 환경에서는 rate limit 비활성
        if request.headers.get("X-Test-Client"):
            return await call_next(request)

        path = request.url.path
        ip = request.client.host if request.client else "unknown"

        if "/auth/login" in path or "/auth/register" in path:
            limit = 20  # 인증: 분당 20회
        else:
            limit = self.max_requests

        now = time.time()
        key = f"{ip}:{path.split('/')[2] if len(path.split('/')) > 2 else 'root'}"

        # 만료된 요청 제거
        self._requests[key] = [t for t in self._requests[key] if now - t < self.window]

        # 비어있는 키 정리 (메모리 누수 방지)
        if not self._requests[key]:
            del self._requests[key]
            return await call_next(request)

        if len(self._requests[key]) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."},
            )

        self._requests[key].append(now)

        # 주기적으로 오래된 키 전체 정리 (1000개 이상일 때)
        if len(self._requests) > 1000:
            stale_keys = [k for k, v in self._requests.items() if not v or now - v[-1] > self.window]
            for k in stale_keys:
                del self._requests[k]

        return await call_next(request)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """전역 에러 핸들링"""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unhandled error: {request.url.path}")
            return JSONResponse(
                status_code=500,
                content={"detail": "서버 내부 오류가 발생했습니다."},
            )
