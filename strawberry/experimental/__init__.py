try:
    from . import pydantic
except ImportError:
    pass
else:
    __all__ = ["pydantic"]
