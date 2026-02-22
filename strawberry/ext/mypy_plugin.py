from __future__ import annotations

import warnings

from mypy.plugin import Plugin


class StrawberryPlugin(Plugin):
    pass


def plugin(version: str) -> type[StrawberryPlugin]:
    warnings.warn(
        "The strawberry mypy plugin is deprecated and no longer needed. "
        "Remove 'strawberry.ext.mypy_plugin' from your mypy plugins.",
        DeprecationWarning,
        stacklevel=1,
    )
    return StrawberryPlugin
