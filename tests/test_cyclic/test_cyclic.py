import textwrap

import strawberry
from strawberry.printer import print_type


def test_cyclic_import():
    from .type_a import TypeA
    from .type_b import TypeB

    @strawberry.type
    class Query:
        a: TypeA
        b: TypeB

    assert (
        print_type(Query(None, None))
        == textwrap.dedent(
            """
            type Query {
              a: TypeA!
              b: TypeB!
            }
            """
        ).strip()
    )

    assert (
        print_type(TypeA())
        == textwrap.dedent(
            """
            type TypeA {
              typeB: TypeB!
            }
            """
        ).strip()
    )

    assert (
        print_type(TypeB())
        == textwrap.dedent(
            """
            type TypeB {
              typeA: TypeA!
            }
            """
        ).strip()
    )
