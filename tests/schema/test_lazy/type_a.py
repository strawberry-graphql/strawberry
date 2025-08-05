from typing import TYPE_CHECKING, Annotated, Optional

import strawberry

if TYPE_CHECKING:
    from .type_b import TypeB


@strawberry.type
class TypeA:
    list_of_b: Optional[
        list[Annotated["TypeB", strawberry.lazy("tests.schema.test_lazy.type_b")]]
    ] = None

    @strawberry.field
    def type_b(self) -> Annotated["TypeB", strawberry.lazy(".type_b")]:
        from .type_b import TypeB

        return TypeB()
