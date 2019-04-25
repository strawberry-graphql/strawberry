import textwrap

import strawberry


def test_cyclic_import():
    from .type_a import TypeA
    from .type_b import TypeB

    @strawberry.type
    class Query:
        a: TypeA
        b: TypeB

    assert (
        repr(Query(None, None))
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
        repr(TypeA())
        == textwrap.dedent(
            """
            type TypeA {
              typeB: TypeB!
            }
            """
        ).strip()
    )

    assert (
        repr(TypeB())
        == textwrap.dedent(
            """
            type TypeB {
              typeA: TypeA!
            }
            """
        ).strip()
    )
