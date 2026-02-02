import enum
import textwrap
from typing import Annotated

import strawberry
from strawberry.printer import print_schema


@strawberry.enum
class LazyEnum(enum.Enum):
    BREAD = "BREAD"


def test_lazy_enum():
    @strawberry.type
    class Query:
        a: Annotated[
            "LazyEnum", strawberry.lazy("tests.schema.test_lazy_types.test_lazy_enums")
        ]

    expected = """
    enum LazyEnum {
      BREAD
    }

    type Query {
      a: LazyEnum!
    }
    """

    schema = strawberry.Schema(Query)

    assert print_schema(schema) == textwrap.dedent(expected).strip()
