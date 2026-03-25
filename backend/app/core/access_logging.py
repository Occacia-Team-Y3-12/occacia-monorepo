from __future__ import annotations

import time

import structlog
from asgi_correlation_id import correlation_id
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class AccessLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, exclude_paths: set[str] | None = None) -> None:
        super().__init__(app)
        self.exclude_paths = exclude_paths or set()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        logger = structlog.get_logger("http.access")
        start = time.perf_counter()
        route = request.scope.get("route")
        route_name = getattr(route, "name", None)
        route_path = getattr(route, "path", None)

        log_context = {
            "method": request.method,
            "path": request.url.path,
            "route_name": route_name,
            "route_path": route_path,
            "request_id": correlation_id.get(),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        actor = getattr(request.state, "actor", None)
        if actor:
            log_context["actor"] = actor

        logger.debug("request.start", **log_context)

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "request.error",
                **log_context,
                status_code=500,
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        status_code = response.status_code
        if status_code >= 500:
            log_fn = logger.error
        elif status_code >= 400:
            log_fn = logger.warning
        else:
            log_fn = logger.info

        log_fn("request.end", **log_context, status_code=status_code, duration_ms=duration_ms)
        return response
