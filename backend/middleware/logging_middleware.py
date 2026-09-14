import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from config.settings import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Production-grade logging middleware that records:
    - Unique Correlation / Request ID for traceability
    - Client IP address and HTTP method/path
    - Response HTTP status code
    - Execution time (in milliseconds)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        client_host = request.client.host if request.client else "unknown"
        path_with_query = request.url.path + (f"?{request.url.query}" if request.url.query else "")

        logger.info(
            f"--> [{request_id[:8]}] {request.method} {path_with_query} from {client_host}"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            status_code = response.status_code
            log_msg = (
                f"<-- [{request_id[:8]}] {request.method} {path_with_query} "
                f"Status: {status_code} ({duration_ms:.2f}ms)"
            )

            if status_code >= 500:
                logger.error(log_msg)
            elif status_code >= 400:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"<-- [{request_id[:8]}] {request.method} {path_with_query} "
                f"FAILED with unhandled exception: {exc} ({duration_ms:.2f}ms)",
                exc_info=True,
            )
            raise exc
