import typing
from importlib import import_module

import strawberry


if typing.TYPE_CHECKING:
    from .type_a import TypeA


@strawberry.type
class TypeB:
    @strawberry.field(
        type=lambda: import_module(".type_a", __package__).TypeA  # type: ignore
    )
    def type_a(self, info) -> "TypeA":
        from .type_a import TypeA

        return TypeA()
