import typing
from importlib import import_module

import strawberry


if typing.TYPE_CHECKING:
    from .type_b import TypeB


@strawberry.type
class TypeA:
    @strawberry.field(
        type=lambda: import_module(".type_b", __package__).TypeB  # type: ignore
    )
    def type_b(self, info) -> "TypeB":
        from .type_b import TypeB

        return TypeB()
