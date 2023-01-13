import enum
import textwrap
from typing import TYPE_CHECKING

import pytest

import strawberry
from strawberry.printer import print_schema

if TYPE_CHECKING:
    import tests


@strawberry.enum
class LazyEnum(enum.Enum):
    BREAD = "BREAD"


def test_lazy_enum():
    with pytest.deprecated_call():

        @strawberry.type
        class Query:
            a: strawberry.LazyType[
                "LazyEnum", "tests.schema.test_lazy_types.test_lazy_enums"
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
