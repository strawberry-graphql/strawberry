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
