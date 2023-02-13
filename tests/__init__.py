# Starlite is only available on python 3.8+
try:
    import starlite  # noqa: F401

    IS_STARLITE_INSTALLED: bool = False
except ModuleNotFoundError:
    IS_STARLITE_INSTALLED: bool = True
