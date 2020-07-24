import typing

import strawberry


if typing.TYPE_CHECKING:
    import tests

    from .type_a import TypeA


@strawberry.type
class TypeB:
    @strawberry.field()
    def type_a(self, info) -> strawberry.LazyType["TypeA", "tests.test_cyclic.type_a"]:
        from .type_a import TypeA

        return TypeA()
