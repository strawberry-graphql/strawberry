from typing import Callable, Optional

from mypy.plugin import ClassDefContext, Plugin
from mypy.plugins import dataclasses


class StrawberryPlugin(Plugin):
    def get_class_decorator_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        if any(
            strawberry_decorator in fullname
            for strawberry_decorator in {
                "strawberry.type",
                "strawberry.federation.type",
                "strawberry.input",
                "strawberry.interface",
            }
        ):
            return dataclasses.dataclass_class_maker_callback
        return None


def plugin(version: str):
    return StrawberryPlugin
