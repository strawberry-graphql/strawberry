try:
    from . import pydantic
except ImportError as e:
    print("ImportError: ", e)
    pass
else:
    __all__ = ["pydantic"]
