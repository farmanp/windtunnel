"""Retry policy and execution utilities."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Literal, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for execution retries."""

    max_attempts: int
    strategy: Literal["fixed", "exponential"]
    delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0

    @classmethod
    def from_dict(cls, data: dict) -> "RetryConfig":
        """Create a RetryConfig from a dictionary."""
        return cls(
            max_attempts=data.get("max_attempts", 3),
            strategy=data.get("strategy", "fixed"),
            delay_seconds=data.get("delay_seconds", 1.0),
            max_delay_seconds=data.get("max_delay_seconds", 30.0),
        )


async def with_retry(
    func: Callable[[], Awaitable[T]],
    config: RetryConfig,
    is_retryable: Callable[[Exception], bool] = lambda e: True,
    should_retry_result: Callable[[T], bool] = lambda r: False,
    on_attempt: Callable[[int, T | None, Exception | None, float], None] | None = None,
) -> T:
    """Execute an async function with retry logic.

    Args:
        func: The async function to execute.
        config: Retry configuration.
        is_retryable: Function that returns True if Exception should trigger a retry.
        should_retry_result: Function that returns True if the result should trigger a retry.
        on_attempt: Optional callback called after each attempt with 
            (attempt_idx, result, exception, duration_ms).

    Returns:
        The result of the successful function execution.

    Raises:
        The last exception caught if all retry attempts fail.
    """
    last_exception: Exception | None = None
    last_result: T | None = None
    
    for attempt in range(1, config.max_attempts + 1):
        start_time = time.perf_counter()
        try:
            result = await func()
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            if on_attempt:
                on_attempt(attempt, result, None, duration_ms)

            if attempt < config.max_attempts and should_retry_result(result):
                last_result = result
                # Fall through to sleep and retry
            else:
                return result
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            last_exception = e
            
            if on_attempt:
                on_attempt(attempt, None, e, duration_ms)

            if attempt == config.max_attempts or not is_retryable(e):
                break

            # If it's a retryable exception, we clear the last result if any
            last_result = None
            
            # Calculate delay
            delay = _calculate_delay(config, attempt)
            logger.debug(
                f"Attempt {attempt}/{config.max_attempts} failed with exception: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)
            continue

        # If we got here, it means should_retry_result returned True
        delay = _calculate_delay(config, attempt)
        logger.debug(
            f"Attempt {attempt}/{config.max_attempts} returned retryable result. "
            f"Retrying in {delay:.2f}s..."
        )
        await asyncio.sleep(delay)

    if last_exception:
        raise last_exception
    
    return last_result  # type: ignore


def _calculate_delay(config: RetryConfig, attempt: int) -> float:
    """Calculate delay for the next attempt."""
    if config.strategy == "exponential":
        return min(
            config.delay_seconds * (2 ** (attempt - 1)),
            config.max_delay_seconds,
        )
    return config.delay_seconds
