# Starlite is only available on python 3.8+
try:

    IS_STARLITE_INSTALLED: bool = False
except ModuleNotFoundError:
    IS_STARLITE_INSTALLED: bool = True

__all__ = ["IS_STARLITE_INSTALLED"]
