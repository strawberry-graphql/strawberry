import typing

import strawberry


if typing.TYPE_CHECKING:
    from .type_b import TypeB


@strawberry.type
class TypeA:
    @strawberry.field
    def type_b(self, info) -> "TypeB":
        from .type_b import TypeB

        return TypeB()
