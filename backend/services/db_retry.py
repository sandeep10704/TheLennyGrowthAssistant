import asyncio
import functools
import random
from typing import Callable, TypeVar, Any, Tuple, Type
from sqlalchemy.exc import (
    OperationalError,
    DBAPIError,
    InterfaceError,
    DisconnectionError,
)
from config.settings import settings, logger

T = TypeVar("T")

# Transient database exception types that warrant retry
TRANSIENT_DB_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    OperationalError,
    DBAPIError,
    InterfaceError,
    DisconnectionError,
    ConnectionResetError,
    ConnectionRefusedError,
    TimeoutError,
    OSError,
)

# Dynamically include asyncpg exceptions if asyncpg is imported
try:
    import asyncpg
    TRANSIENT_DB_EXCEPTIONS = TRANSIENT_DB_EXCEPTIONS + (
        asyncpg.PostgresConnectionError,
        asyncpg.CannotConnectNowError,
        asyncpg.ConnectionDoesNotExistError,
        asyncpg.InterfaceError,
        asyncpg.TooManyConnectionsError,
    )
except ImportError:
    pass


async def execute_with_db_retry(
    operation: Callable[..., Any],
    *args: Any,
    max_retries: int = settings.DB_MAX_RETRIES,
    base_delay: float = settings.DB_RETRY_BASE_DELAY,
    max_delay: float = settings.DB_RETRY_MAX_DELAY,
    operation_name: str = "Database Operation",
    **kwargs: Any,
) -> Any:
    """
    Executes an async database operation with exponential backoff and jitter
    for transient connection failures (especially critical for Supabase poolers).
    """
    attempt = 0
    last_exception: Exception = None  # type: ignore

    while attempt < max_retries:
        try:
            return await operation(*args, **kwargs)
        except TRANSIENT_DB_EXCEPTIONS as exc:
            attempt += 1
            last_exception = exc

            if attempt >= max_retries:
                logger.error(
                    f"[{operation_name}] Failed after {attempt} attempts: {exc}",
                    exc_info=True,
                )
                raise exc

            # Calculate exponential backoff with randomized jitter
            jitter = random.uniform(0.05, 0.25)
            delay = min(max_delay, base_delay * (2 ** (attempt - 1))) + jitter

            logger.warning(
                f"[{operation_name}] Transient error (attempt {attempt}/{max_retries}): {exc}. "
                f"Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)
        except Exception as non_transient_exc:
            # Non-transient errors (e.g. syntax errors, unique constraint errors) should not be retried
            logger.debug(f"[{operation_name}] Non-transient exception encountered: {non_transient_exc}")
            raise non_transient_exc

    if last_exception:
        raise last_exception


def with_db_retry(
    max_retries: int = settings.DB_MAX_RETRIES,
    base_delay: float = settings.DB_RETRY_BASE_DELAY,
    max_delay: float = settings.DB_RETRY_MAX_DELAY,
    operation_name: str = "Database Operation",
):
    """
    Decorator for async methods to automatically retry on transient database errors.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or func.__name__
            return await execute_with_db_retry(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                operation_name=op_name,
                **kwargs,
            )
        return wrapper
    return decorator
