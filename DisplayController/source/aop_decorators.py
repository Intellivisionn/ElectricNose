import time
import functools

def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] Calling: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def catch_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR] Exception in {func.__name__}: {e}")
    return wrapper

def measure_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"[TIME] {func.__name__} took {duration:.3f}s")
        return result
    return wrapper
