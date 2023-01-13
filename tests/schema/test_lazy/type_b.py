from typing import TYPE_CHECKING
from typing_extensions import Annotated

import strawberry

if TYPE_CHECKING:
    from .type_a import TypeA
else:
    TypeA = Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy.type_a")]


@strawberry.type
class TypeB:
    @strawberry.field()
    def type_a(
        self,
    ) -> TypeA:
        from .type_a import TypeA

        return TypeA()
