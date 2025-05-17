import functools
import logging
import time
import inspect

# Configure a logger for AOP
logger = logging.getLogger("aop")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log_call(func):
    """
    Logs entry & exit of sync or async functions.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # drop self from args when printing
            params = [repr(a) for a in args[1:]] + [f"{k}={v!r}" for k,v in kwargs.items()]
            logger.info(f"ENTER {func.__qualname__}({', '.join(params)})")
            result = await func(*args, **kwargs)
            logger.info(f"EXIT  {func.__qualname__} -> {result!r}")
            return result
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            params = [repr(a) for a in args[1:]] + [f"{k}={v!r}" for k,v in kwargs.items()]
            logger.info(f"ENTER {func.__qualname__}({', '.join(params)})")
            result = func(*args, **kwargs)
            logger.info(f"EXIT  {func.__qualname__} -> {result!r}")
            return result
        return sync_wrapper


def catch_errors(func):
    """
    Wraps sync or async functions to catch and log exceptions.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception:
                logger.exception(f"Exception in {func.__qualname__}")
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.exception(f"Exception in {func.__qualname__}")
        return sync_wrapper


def measure_time(func):
    """
    Measures execution time of sync or async functions.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            logger.info(f"TIMING {func.__qualname__}: {time.time() - start:.3f}s")
            return result
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            logger.info(f"TIMING {func.__qualname__}: {time.time() - start:.3f}s")
            return result
        return sync_wrapper