from typing import Callable, Any, TypeVar

T = TypeVar("T")

from anicli.config import dp

CONCATENATE_ARGS = lambda *args: (" ".join(list(args)),)  # noqa

def check_cache(key: T, function: Callable[[], T]) -> T:
    if not (results := dp.state_dispenser.get_cache(key)):
        results = function()
        dp.state_dispenser.cache_object(key, results)
    return results
