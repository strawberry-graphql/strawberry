try:
    from . import pydantic
    __all__ = ["pydantic"]
except ImportError:
    pass
try:
    from . import pydantic2
    # Support for pydantic2 is highly experimental and the interface will change
    # We don't recommend using it yet
    __all__ = ["pydantic2"]
except ImportError as e:
    pass
