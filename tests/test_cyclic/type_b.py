import typing

import strawberry


if typing.TYPE_CHECKING:
    from .type_a import TypeA


@strawberry.type
class TypeB:
    @strawberry.field
    def type_a(self, info) -> "TypeA":
        from .type_a import TypeA

        return TypeA()
