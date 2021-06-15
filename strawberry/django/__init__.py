try:
    # import modules and objects from external strawberry-graphql-django
    # package so that it can be used through strawberry.django namespace
    from strawberry_django import *  # noqa: F401, F403
except ModuleNotFoundError:
    import importlib

    def __getattr__(name):
        # try to import submodule and raise exception only if it does not exist
        import_symbol = f"{__name__}.{name}"
        try:
            return importlib.import_module(import_symbol)
        except ModuleNotFoundError:
            raise AttributeError(
                f"Attempted import of {import_symbol} failed. Make sure to install the"
                "'strawberry-graphql-django' package to use the Strawberry Django "
                "extension API."
            )
