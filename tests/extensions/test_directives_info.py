from enum import Enum
from typing import Annotated, Optional

import strawberry
from strawberry.directive import DirectiveLocation, DirectiveValue
from strawberry.extensions.directives import _has_input_object_arguments


@strawberry.input
class Options:
    suffix: str


@strawberry.enum
class Color(Enum):
    RED = "red"


def test_directives_with_input_object_arguments_build_the_info():
    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def scalars(value: DirectiveValue[str], times: int, color: Color) -> str:
        return value

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def options(
        value: DirectiveValue[str], options: Optional[list[Optional[Options]]]
    ) -> str:
        return value

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def lazy_enum(
        value: DirectiveValue[str],
        color: Annotated[
            "Color", strawberry.lazy("tests.extensions.test_directives_info")
        ],
    ) -> str:
        return value

    assert not _has_input_object_arguments(scalars)
    assert _has_input_object_arguments(options)
    assert not _has_input_object_arguments(lazy_enum)


def test_directive_info_on_introspection_field():
    received_info: list[strawberry.Info] = []

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def uppercase(value: DirectiveValue[str], info: strawberry.Info) -> str:
        received_info.append(info)
        return value.upper()

    @strawberry.type
    class Query:
        hello: str = "world"

    schema = strawberry.Schema(query=Query, directives=[uppercase])
    result = schema.execute_sync("{ __typename @uppercase }")

    assert result.errors is None
    assert result.data == {"__typename": "QUERY"}
    assert received_info[0].python_name == "typename"
    assert received_info[0].return_type is str
