from typing import Callable, Optional

from mypy.plugin import AnalyzeTypeContext, ClassDefContext, Plugin
from mypy.plugins import dataclasses
from mypy.types import Type


def lazy_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


class StrawberryPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str):
        if fullname == "strawberry.lazy_type.LazyType":
            return lazy_type_analyze_callback

        return None

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
