import sys
from typing import List, Optional

import pytest

from typing_extensions import Annotated

import strawberry
from strawberry.exceptions import MultipleStrawberryArgumentsError
from strawberry.types.types import undefined


def test_basic_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: str, optional_argument: Optional[str]) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 2

    assert definition.fields[0].arguments[0].name == "argument"
    assert definition.fields[0].arguments[0].type == str
    assert definition.fields[0].arguments[0].is_optional is False

    assert definition.fields[0].arguments[1].name == "optionalArgument"
    assert definition.fields[0].arguments[1].type == str
    assert definition.fields[0].arguments[1].is_optional


def test_input_type_as_argument():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, input: Input, optional_input: Optional[Input]) -> str:
            return input.name

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 2

    assert definition.fields[0].arguments[0].name == "input"
    assert definition.fields[0].arguments[0].type == Input
    assert definition.fields[0].arguments[0].is_optional is False

    assert definition.fields[0].arguments[1].name == "optionalInput"
    assert definition.fields[0].arguments[1].type == Input
    assert definition.fields[0].arguments[1].is_optional


def test_arguments_lists():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def names(self, inputs: List[Input]) -> List[str]:
            return [input.name for input in inputs]

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    assert definition.fields[0].arguments[0].name == "inputs"
    assert definition.fields[0].arguments[0].type is None
    assert definition.fields[0].arguments[0].is_list
    assert definition.fields[0].arguments[0].is_optional is False
    assert definition.fields[0].arguments[0].child.type == Input
    assert definition.fields[0].arguments[0].child.is_optional is False


def test_arguments_lists_of_optionals():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def names(self, inputs: List[Optional[Input]]) -> List[str]:
            return [input.name for input in inputs if input]

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    assert definition.fields[0].arguments[0].name == "inputs"
    assert definition.fields[0].arguments[0].type is None
    assert definition.fields[0].arguments[0].is_list
    assert definition.fields[0].arguments[0].is_optional is False
    assert definition.fields[0].arguments[0].child.type == Input
    assert definition.fields[0].arguments[0].child.is_optional is True


def test_basic_arguments_on_resolver():
    def name_resolver(
        id: strawberry.ID, argument: str, optional_argument: Optional[str]
    ) -> str:
        return "Name"

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=name_resolver)

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 3

    assert definition.fields[0].arguments[0].name == "id"
    assert definition.fields[0].arguments[0].type == strawberry.ID
    assert definition.fields[0].arguments[0].is_optional is False

    assert definition.fields[0].arguments[1].name == "argument"
    assert definition.fields[0].arguments[1].type == str
    assert definition.fields[0].arguments[1].is_optional is False

    assert definition.fields[0].arguments[2].name == "optionalArgument"
    assert definition.fields[0].arguments[2].type == str
    assert definition.fields[0].arguments[2].is_optional


def test_arguments_when_extending_a_type():
    def name_resolver(
        id: strawberry.ID, argument: str, optional_argument: Optional[str]
    ) -> str:
        return "Name"

    @strawberry.type
    class NameQuery:
        name: str = strawberry.field(resolver=name_resolver)

    @strawberry.type
    class Query(NameQuery):
        pass

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields) == 1
    assert len(definition.fields[0].arguments) == 3

    assert definition.fields[0].arguments[0].name == "id"
    assert definition.fields[0].arguments[0].type == strawberry.ID
    assert definition.fields[0].arguments[0].is_optional is False

    assert definition.fields[0].arguments[1].name == "argument"
    assert definition.fields[0].arguments[1].type == str
    assert definition.fields[0].arguments[1].is_optional is False

    assert definition.fields[0].arguments[2].name == "optionalArgument"
    assert definition.fields[0].arguments[2].type == str
    assert definition.fields[0].arguments[2].is_optional


def test_arguments_when_extending_multiple_types():
    def name_resolver(id: strawberry.ID) -> str:
        return "Name"

    def name_2_resolver(id: strawberry.ID) -> str:
        return "Name 2"

    @strawberry.type
    class NameQuery:
        name: str = strawberry.field(permission_classes=[], resolver=name_resolver)

    @strawberry.type
    class ExampleQuery:
        name_2: str = strawberry.field(permission_classes=[], resolver=name_2_resolver)

    @strawberry.type
    class RootQuery(NameQuery, ExampleQuery):
        pass

    definition = RootQuery._type_definition

    assert definition.name == "RootQuery"

    assert len(definition.fields) == 2
    assert len(definition.fields[0].arguments) == 1

    assert definition.fields[0].arguments[0].name == "id"
    assert definition.fields[0].arguments[0].type == strawberry.ID
    assert definition.fields[0].arguments[0].is_optional is False

    assert len(definition.fields[1].arguments) == 1

    assert definition.fields[1].name == "name2"
    assert definition.fields[1].arguments[0].name == "id"
    assert definition.fields[1].arguments[0].type == strawberry.ID
    assert definition.fields[1].arguments[0].is_optional is False


def test_argument_with_default_value_none():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str] = None) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.name == "argument"
    assert argument.type == str
    assert argument.is_optional is True
    assert argument.description is None
    assert argument.default_value is None


def test_argument_with_default_value_undefined():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str]) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.name == "argument"
    assert argument.type == str
    assert argument.is_optional is True
    assert argument.description is None
    assert argument.default_value == undefined


def test_annotated_argument_on_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(  # type: ignore
            argument: Annotated[
                str,
                strawberry.argument(description="This is a description"),  # noqa: F722
            ]
        ) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.name == "argument"
    assert argument.type == str
    assert argument.is_optional is False
    assert argument.description == "This is a description"


def test_annotated_optional_arguments_on_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(  # type: ignore
            argument: Annotated[
                Optional[str],
                strawberry.argument(description="This is a description"),  # noqa: F722
            ]
        ) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.name == "argument"
    assert argument.type == str
    assert argument.is_optional is True
    assert argument.description == "This is a description"


def test_annotated_argument_with_default_value():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(  # type: ignore
            argument: Annotated[
                str,
                strawberry.argument(description="This is a description"),  # noqa: F722
            ] = "Patrick"
        ) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.name == "argument"
    assert argument.type == str
    assert argument.is_optional is False
    assert argument.description == "This is a description"
    assert argument.default_value == "Patrick"


def test_multiple_annotated_arguments_exception():
    with pytest.raises(MultipleStrawberryArgumentsError) as error:

        @strawberry.field
        def name(  # type: ignore
            argument: Annotated[
                str,
                strawberry.argument(description="This is a description"),  # noqa: F722
                strawberry.argument(description="Another description"),  # noqa: F722
            ]
        ) -> str:
            return "Name"

    assert str(error.value) == (
        "Annotation for argument `argument` "
        "on field `name` cannot have multiple "
        "`strawberry.argument`s"
    )


def test_annotated_with_other_information():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(  # type: ignore
            argument: Annotated[str, "Some other info"]  # noqa: F722
        ) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.name == "argument"
    assert argument.type == str
    assert argument.is_optional is False
    assert argument.description is None


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="Annotated type was added in python 3.9",
)
def test_annotated_python_39():
    from typing import Annotated

    @strawberry.type
    class Query:
        @strawberry.field
        def name(  # type: ignore
            argument: Annotated[
                str,
                strawberry.argument(description="This is a description"),  # noqa: F722
            ]
        ) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.name == "argument"
    assert argument.type == str
    assert argument.is_optional is False
    assert argument.description == "This is a description"
