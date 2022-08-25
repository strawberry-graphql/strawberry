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
      listOfB: [TypeB!]
      done: Boolean!
      typeB: TypeB!
    }

    type TypeB {
      typeA: TypeA!
    }
    """

    schema = strawberry.Schema(Query)
    res = schema.execute_sync(
        """
    query MyQuery {
      a {
        typeB {
          typeA {
            done
          }
        }
      }
    }
    """,
        root_value=Query(a=TypeA(), b=TypeB()),
    )
    assert res.errors is None
    assert res.data["a"]["typeB"]["typeA"]["done"]
    expected = textwrap.dedent(expected).strip()
    schema = print_schema(schema).splitlines()
    for line in expected.splitlines():
        assert line in schema
