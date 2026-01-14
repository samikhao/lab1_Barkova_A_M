import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from structlog.contextvars import bind_contextvars, clear_contextvars
import structlog

from .metrics import HTTP_IN_PROGRESS, HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION

log = structlog.get_logger()


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path or request.url.path


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        start = time.perf_counter()

        path_tmpl = _route_template(request)

        clear_contextvars()
        bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=path_tmpl,
        )

        HTTP_IN_PROGRESS.labels(request.method, path_tmpl).inc()

        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            log.exception("unhandled_error")
            raise
        finally:
            dur = time.perf_counter() - start
            HTTP_IN_PROGRESS.labels(request.method, path_tmpl).dec()

            HTTP_REQUESTS_TOTAL.labels(
                request.method, path_tmpl, str(status_code)
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                request.method, path_tmpl, str(status_code)
            ).observe(dur)

            log.info(
                "request",
                status_code=status_code,
                duration_ms=round(dur * 1000, 2),
                client_host=request.client.host if request.client else None,
            )

            clear_contextvars()
