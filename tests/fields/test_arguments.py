import sys
from typing import List, Optional

import pytest

from typing_extensions import Annotated

import strawberry
from strawberry.arguments import UNSET
from strawberry.exceptions import MultipleStrawberryArgumentsError
from strawberry.type import StrawberryList, StrawberryOptional


def test_basic_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: str, optional_argument: Optional[str]) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    [argument1, argument2] = definition.fields[0].arguments

    assert argument1.graphql_name == "argument"
    assert argument1.type is str

    assert argument2.graphql_name == "optionalArgument"
    assert isinstance(argument2.type, StrawberryOptional)
    assert argument2.type.of_type is str


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

    [argument1, argument2] = definition.fields[0].arguments

    assert argument1.graphql_name == "input"
    assert argument1.type is Input

    assert argument2.graphql_name == "optionalInput"
    assert isinstance(argument2.type, StrawberryOptional)
    assert argument2.type.of_type is Input


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

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "inputs"
    assert isinstance(argument.type, StrawberryList)
    assert argument.type.of_type is Input


def test_arguments_lists_of_optionals():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def names(self, inputs: List[Optional[Input]]) -> List[str]:
            return [input_.name for input_ in inputs if input_ is not None]

    definition = Query._type_definition

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "inputs"
    assert isinstance(argument.type, StrawberryList)
    assert isinstance(argument.type.of_type, StrawberryOptional)
    assert argument.type.of_type.of_type is Input


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

    [argument1, argument2, argument3] = definition.fields[0].arguments

    assert argument1.graphql_name == "id"
    assert argument1.type is strawberry.ID

    assert argument2.graphql_name == "argument"
    assert argument2.type is str

    assert argument3.graphql_name == "optionalArgument"
    assert isinstance(argument3.type, StrawberryOptional)
    assert argument3.type.of_type is str


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

    [argument1, argument2, argument3] = definition.fields[0].arguments

    assert argument1.graphql_name == "id"
    assert argument1.type is strawberry.ID

    assert argument2.graphql_name == "argument"
    assert argument2.type is str

    assert argument3.graphql_name == "optionalArgument"
    assert isinstance(argument3.type, StrawberryOptional)
    assert argument3.type.of_type is str


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

    [argument1] = definition.fields[0].arguments

    assert argument1.graphql_name == "id"
    assert argument1.type is strawberry.ID

    [argument2] = definition.fields[1].arguments

    assert definition.fields[1].graphql_name == "name2"
    assert argument2.graphql_name == "id"
    assert argument2.type is strawberry.ID


def test_argument_with_default_value_none():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str] = None) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "argument"
    assert argument.default is None
    assert argument.description is None
    assert isinstance(argument.type, StrawberryOptional)
    assert argument.type.of_type is str


def test_argument_with_default_value_undefined():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str]) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "argument"
    assert argument.default is UNSET
    assert argument.description is None
    assert isinstance(argument.type, StrawberryOptional)
    assert argument.type.of_type is str


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

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "argument"
    assert argument.description == "This is a description"
    assert argument.type is str


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

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "argument"
    assert argument.description == "This is a description"
    assert isinstance(argument.type, StrawberryOptional)
    assert argument.type.of_type is str


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

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "argument"
    assert argument.description == "This is a description"
    assert argument.type is str
    assert argument.default == "Patrick"


def test_annotated_argument_with_rename():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(  # type: ignore
            arg: Annotated[
                str,
                strawberry.argument(name="argument"),  # noqa: F722
            ] = "Patrick"
        ) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.graphql_name == "argument"
    assert argument.python_name == "arg"
    assert argument.type is str
    assert argument.description is None
    assert argument.default == "Patrick"


@pytest.mark.xfail(reason="Can't get field name from argument")
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

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "argument"
    assert argument.description is None
    assert argument.type is str


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

    [argument] = definition.fields[0].arguments

    assert argument.graphql_name == "argument"
    assert argument.description == "This is a description"
    assert argument.type is str
