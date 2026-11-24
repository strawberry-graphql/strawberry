import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import pydantic as pydantic

    __all__ = ["pydantic"]
else:
    # hidden from type checkers, which would otherwise accept any attribute of
    # the module
    def __getattr__(name: str) -> object:
        # the pydantic integration depends on the optional pydantic package, which
        # is slow to import, so we only import it on first access instead of when
        # importing strawberry
        if name == "pydantic":
            try:
                return importlib.import_module(f"{__name__}.pydantic")
            except ImportError as exc:
                # an AttributeError keeps `hasattr` and `getattr` with a default
                # working when pydantic isn't installed
                raise AttributeError(str(exc)) from exc

        # star imports (and introspection tools) read `__all__`, which only lists
        # the pydantic integration when it can be imported, so that
        # `from strawberry.experimental import *` keeps working without pydantic
        if name == "__all__":
            try:
                importlib.import_module(f"{__name__}.pydantic")
            except ImportError:
                return []

            return ["pydantic"]

        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
