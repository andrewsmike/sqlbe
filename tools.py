from functools import wraps

__all__ = [
    'id_memoize',
]

def id_memoize(func):
    func._cache = {}
    @wraps(func)
    def memoized_call(*args, **kwargs):
        args_key = tuple(map(id, args))
        kwargs_key = tuple(sorted(
            (k, id(v))
            for k, v in kwargs.items()
        ))
        key = args_key, kwargs_key
        if key not in func._cache:
            func._cache[key] = func(*args, **kwargs)
        return func._cache[key]

    return memoized_call
