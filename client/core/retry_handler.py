"""
ClawSave Client - 重试处理器

提供网络请求重试装饰器，支持指数退避策略。
"""

import time
import functools
import requests.exceptions
from typing import Callable, Optional, Type, Tuple, Any
from logging import getLogger

logger = getLogger(__name__)


class RetryExhausted(Exception):
    """重试次数耗尽异常"""
    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"重试 {attempts} 次后仍失败: {last_error}")


def with_retry(
    func: Optional[Callable] = None,
    *,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable:
    """
    重试装饰器，支持直接使用或带参数使用。

    Args:
        func: 被装饰的函数（直接使用时）
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        backoff_factor: 退避因子（每次重试延迟乘以此因子）
        max_delay: 最大延迟（秒）
        exceptions: 触发重试的异常类型元组（默认为网络异常）
        on_retry: 重试回调函数 (attempt, error)

    Returns:
        装饰后的函数

    Example:
        # 直接使用（默认参数）
        @with_retry
        def network_operation():
            ...

        # 带参数使用
        @with_retry(max_retries=5, retry_delay=2.0)
        def network_operation():
            ...
    """
    # 默认网络异常
    if exceptions is None:
        exceptions = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
            ConnectionError,
            TimeoutError,
            OSError,
        )

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            delay = retry_delay
            last_error: Optional[Exception] = None

            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_error = e

                    if attempt < max_retries:
                        # 调用重试回调
                        if on_retry:
                            try:
                                on_retry(attempt, e)
                            except Exception:
                                pass
                        else:
                            logger.warning(
                                f"操作失败 (尝试 {attempt}/{max_retries}): {e}, "
                                f"{delay:.1f}秒后重试..."
                            )

                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        # 最后一次尝试失败
                        logger.error(
                            f"操作失败，已重试 {max_retries} 次: {e}"
                        )

            raise RetryExhausted(max_retries, last_error)

        return wrapper

    # 支持两种使用方式：@with_retry 和 @with_retry(...)
    if func is not None:
        return decorator(func)
    return decorator


def retry_on_network_error(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Callable:
    """
    网络错误重试装饰器（简化版）。

    专门处理 requests 库的网络异常。

    Args:
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        backoff_factor: 退避因子

    Returns:
        装饰后的函数
    """
    return with_retry(
        max_retries=max_retries,
        retry_delay=retry_delay,
        backoff_factor=backoff_factor
    )
