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
        # 인증 관련 엔드포인트는 더 엄격하게
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

        if len(self._requests[key]) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."},
            )

        self._requests[key].append(now)
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
