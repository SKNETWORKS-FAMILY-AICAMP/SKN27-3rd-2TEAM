import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("rimas.http")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = uuid.uuid4().hex[:8]
        start = time.perf_counter()

        logger.info(
            "request",
            extra={
                "req_id": req_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
            },
        )

        try:
            response = await call_next(request)
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info(
                "response",
                extra={"req_id": req_id, "status": response.status_code, "ms": ms},
            )
            response.headers["X-Request-Id"] = req_id
            return response
        except Exception as exc:
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "request_error",
                extra={"req_id": req_id, "ms": ms, "error": str(exc)},
                exc_info=True,
            )
            raise
