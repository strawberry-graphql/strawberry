from typing import TYPE_CHECKING

from typing_extensions import Annotated

import strawberry


if TYPE_CHECKING:
    from .type_a import TypeA


@strawberry.type
class TypeB:
    @strawberry.field()
    def type_a(
        self,
    ) -> Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy_types.type_a")]:
        from .type_a import TypeA

        return TypeA()
