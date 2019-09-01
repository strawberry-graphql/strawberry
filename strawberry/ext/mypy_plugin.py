from typing import Callable, Optional

from mypy.plugin import ClassDefContext, Plugin
from mypy.plugins import dataclasses


class StrawberryPlugin(Plugin):
    def get_class_decorator_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname in {
            "strawberry.type.type",
            "strawberry.type.input",
            "strawberry.type.interface",
        }:
            return dataclasses.dataclass_class_maker_callback
        return None


def plugin(version: str):
    return StrawberryPlugin
