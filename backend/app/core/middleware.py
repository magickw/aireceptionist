"""Request logging middleware with correlation IDs."""

import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip noisy paths
        if request.url.path == "/health" or request.scope.get("type") == "websocket":
            return await call_next(request)

        request_id = uuid.uuid4().hex[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000)

        logger.info(
            "%s %s %s -> %s (%sms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers["X-Request-Id"] = request_id
        return response
