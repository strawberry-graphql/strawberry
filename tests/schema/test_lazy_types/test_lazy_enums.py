import enum
import textwrap
from typing import TYPE_CHECKING

import strawberry
from strawberry.printer import print_schema


if TYPE_CHECKING:
    import tests


@strawberry.enum
class LazyEnum(enum.Enum):
    BREAD = "BREAD"


def test_cyclic_import():
    from .type_b import TypeB

    @strawberry.type
    class Query:
        a: strawberry.LazyType[
            "LazyEnum", "tests.schema.test_lazy_types.test_lazy_enums"
        ]
        b: TypeB

    expected = """
    type Query {
      a: TypeA!
      b: TypeB!
    }

    type TypeA {
      listOfB: [TypeB!]
      typeB: TypeB!
    }

    type TypeB {
      typeA: TypeA!
    }
    """

    schema = strawberry.Schema(Query)

    assert print_schema(schema) == textwrap.dedent(expected).strip()
