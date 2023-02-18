from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    import tests

    from .type_a import TypeA


@strawberry.type
class TypeB:
    @strawberry.field()
    def type_a(
        self,
    ) -> strawberry.LazyType["TypeA", "tests.schema.test_lazy_types.type_a"]:
        from .type_a import TypeA

        return TypeA()
