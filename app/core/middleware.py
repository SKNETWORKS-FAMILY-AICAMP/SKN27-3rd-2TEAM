import logging
import time
import uuid

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("rimas.http")


class LoggingMiddleware:
    """순수 ASGI 미들웨어 — BaseHTTPMiddleware 대신 사용해 StreamingResponse 버퍼링을 방지한다."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
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

        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", req_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info("response", extra={"req_id": req_id, "status": status_code, "ms": ms})
        except Exception as exc:
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "request_error",
                extra={"req_id": req_id, "ms": ms, "error": str(exc)},
                exc_info=True,
            )
            raise
