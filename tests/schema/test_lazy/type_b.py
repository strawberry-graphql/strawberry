from typing import TYPE_CHECKING, List
from typing_extensions import Annotated

import strawberry

if TYPE_CHECKING:
    from .type_a import TypeA
    from .type_c import TypeC

    ListTypeA = List[TypeA]
    ListTypeC = List[TypeC]
else:
    TypeA = Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy.type_a")]
    ListTypeA = List[
        Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy.type_a")]
    ]
    ListTypeC = List[
        Annotated["TypeC", strawberry.lazy("tests.schema.test_lazy.type_c")]
    ]


@strawberry.type
class TypeB:
    @strawberry.field()
    def type_a(
        self,
    ) -> TypeA:
        from .type_a import TypeA

        return TypeA()

    @strawberry.field()
    def type_a_list(
        self,
    ) -> ListTypeA:  # pragma: no cover
        from .type_a import TypeA

        return [TypeA()]

    @strawberry.field()
    def type_c_list(
        self,
    ) -> ListTypeC:  # pragma: no cover
        from .type_c import TypeC

        return [TypeC()]
