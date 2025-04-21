class LoggingAspect:
    @staticmethod
    def log_method(func):
        def wrapper(*args, **kwargs):
            # [LOG] Before calling {className}.{methodName}()
            print(f"[LOG] Before calling {(args[0] if args else None).__class__.__name__ if (args[0] if args else None) else "UnknownClass"}.{func.__name__}()")
            try:
                result = func(*args, **kwargs)
            finally:
                # [LOG] After calling {className}.{methodName}()
                print(f"[LOG] After calling {(args[0] if args else None).__class__.__name__ if (args[0] if args else None) else "UnknownClass"}.{func.__name__}()")
            return result
        return wrapper