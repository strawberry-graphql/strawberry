try:
    from . import pydantic
except ModuleNotFoundError:
    pass
else:
    __all__ = ["pydantic"]
