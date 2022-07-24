import sys


def _gte_310() -> bool:
    return sys.version_info >= (3, 10)
