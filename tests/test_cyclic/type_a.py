import typing

import strawberry


if typing.TYPE_CHECKING:
    import tests

    from .type_b import TypeB


@strawberry.type
class TypeA:
    @strawberry.field()
    def type_b(self, info) -> strawberry.LazyType["TypeB", "tests.test_cyclic.type_b"]:
        from .type_b import TypeB

        return TypeB()
