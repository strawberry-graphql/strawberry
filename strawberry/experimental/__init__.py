try:
    from . import pydantic
except ImportError as e:
    error = e
else:
    __all__ = ["pydantic"]
