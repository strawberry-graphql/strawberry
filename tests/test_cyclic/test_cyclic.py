import textwrap

import strawberry
from strawberry.printer import print_schema


def test_cyclic_import():
    from .type_a import TypeA
    from .type_b import TypeB

    @strawberry.type
    class Query:
        a: TypeA
        b: TypeB

    expected = """
    type Query {
      a: TypeA!
      b: TypeB!
    }

    type TypeA {
      typeB: TypeB!
    }

    type TypeB {
      typeA: TypeA!
    }
    """

    fields = Query._type_definition.fields

    assert fields[0].name == "a"
    assert fields[0].type == TypeA

    assert fields[1].name == "b"
    assert fields[1].type == TypeB

    schema = strawberry.Schema(Query)

    assert print_schema(schema) == textwrap.dedent(expected).strip()
