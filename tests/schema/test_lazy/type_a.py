from typing import TYPE_CHECKING, List, Optional
from typing_extensions import Annotated

import strawberry

if TYPE_CHECKING:
    from .type_b import TypeB

    TypeB_rel = TypeB
    TypeB_abs = TypeB
else:
    TypeB_rel = Annotated["TypeB", strawberry.lazy(".type_b")]
    TypeB_abs = Annotated["TypeB", strawberry.lazy("tests.schema.test_lazy.type_b")]


@strawberry.type
class TypeA:
    list_of_b: Optional[List[TypeB_abs]] = None

    @strawberry.field
    def type_b(self) -> TypeB_rel:
        from .type_b import TypeB

        return TypeB()
