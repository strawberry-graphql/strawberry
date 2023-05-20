try:
    from . import pydantic

    __all__ = ["pydantic"]
except ImportError:
    pass
try:
    from . import pydantic2

    __all__ = ["pydantic2"]
except ImportError as e:
    print(e)
