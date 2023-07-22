try:
    from . import pydantic
except ImportError as e:
    pass
else:
    __all__ = ["pydantic"]
