from typing import Annotated, Optional, Union

import pytest

import strawberry
from strawberry import UNSET
from strawberry.exceptions import (
    InvalidArgumentTypeError,
    MultipleStrawberryArgumentsError,
)
from strawberry.types.base import StrawberryList, StrawberryOptional


def test_basic_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(
            self, argument: str, optional_argument: Optional[str]
        ) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument1, argument2] = definition.fields[0].arguments

    assert argument1.python_name == "argument"
    assert argument1.graphql_name is None
    assert argument1.type is str

    assert argument2.python_name == "optional_argument"
    assert argument2.graphql_name is None
    assert isinstance(argument2.type, StrawberryOptional)
    assert argument2.type.of_type is str


def test_input_type_as_argument():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def name(
            self, input: Input, optional_input: Optional[Input]
        ) -> str:  # pragma: no cover
            return input.name

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument1, argument2] = definition.fields[0].arguments

    assert argument1.python_name == "input"
    assert argument1.graphql_name is None
    assert argument1.type is Input

    assert argument2.python_name == "optional_input"
    assert argument2.graphql_name is None
    assert isinstance(argument2.type, StrawberryOptional)
    assert argument2.type.of_type is Input


def test_arguments_lists():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def names(self, inputs: list[Input]) -> list[str]:  # pragma: no cover
            return [input.name for input in inputs]

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "inputs"
    assert argument.graphql_name is None
    assert isinstance(argument.type, StrawberryList)
    assert argument.type.of_type is Input


def test_arguments_lists_of_optionals():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def names(self, inputs: list[Optional[Input]]) -> list[str]:  # pragma: no cover
            return [input_.name for input_ in inputs if input_ is not None]

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "inputs"
    assert argument.graphql_name is None
    assert isinstance(argument.type, StrawberryList)
    assert isinstance(argument.type.of_type, StrawberryOptional)
    assert argument.type.of_type.of_type is Input


def test_basic_arguments_on_resolver():
    def name_resolver(  # pragma: no cover
        id: strawberry.ID, argument: str, optional_argument: Optional[str]
    ) -> str:
        return "Name"

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=name_resolver)

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument1, argument2, argument3] = definition.fields[0].arguments

    assert argument1.python_name == "id"
    assert argument1.type is strawberry.ID

    assert argument2.python_name == "argument"
    assert argument2.type is str

    assert argument3.python_name == "optional_argument"
    assert isinstance(argument3.type, StrawberryOptional)
    assert argument3.type.of_type is str


def test_arguments_when_extending_a_type():
    def name_resolver(
        id: strawberry.ID, argument: str, optional_argument: Optional[str]
    ) -> str:  # pragma: no cover
        return "Name"

    @strawberry.type
    class NameQuery:
        name: str = strawberry.field(resolver=name_resolver)

    @strawberry.type
    class Query(NameQuery):
        pass

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    assert len(definition.fields) == 1

    [argument1, argument2, argument3] = definition.fields[0].arguments

    assert argument1.python_name == "id"
    assert argument1.type is strawberry.ID

    assert argument2.python_name == "argument"
    assert argument2.type is str

    assert argument3.python_name == "optional_argument"
    assert isinstance(argument3.type, StrawberryOptional)
    assert argument3.type.of_type is str


def test_arguments_when_extending_multiple_types():
    def name_resolver(id: strawberry.ID) -> str:  # pragma: no cover
        return "Name"

    def name_2_resolver(id: strawberry.ID) -> str:  # pragma: no cover
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

    definition = RootQuery.__strawberry_definition__

    assert definition.name == "RootQuery"

    assert len(definition.fields) == 2

    [argument1] = definition.fields[0].arguments

    assert argument1.python_name == "id"
    assert argument1.graphql_name is None
    assert argument1.type is strawberry.ID

    [argument2] = definition.fields[1].arguments

    assert argument2.python_name == "id"
    assert argument2.graphql_name is None
    assert argument2.type is strawberry.ID


def test_argument_with_default_value_none():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str] = None) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
    assert argument.default is None
    assert argument.description is None
    assert isinstance(argument.type, StrawberryOptional)
    assert argument.type.of_type is str


def test_argument_with_default_value_undefined():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str]) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
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
                strawberry.argument(description="This is a description"),
            ],
        ) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
    assert argument.description == "This is a description"
    assert argument.type is str


def test_annotated_optional_arguments_on_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(  # type: ignore
            argument: Annotated[
                Optional[str],
                strawberry.argument(description="This is a description"),
            ],
        ) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
    assert argument.description == "This is a description"
    assert isinstance(argument.type, StrawberryOptional)
    assert argument.type.of_type is str


def test_annotated_argument_with_default_value():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(
            self,
            argument: Annotated[
                str,
                strawberry.argument(description="This is a description"),
            ] = "Patrick",
        ) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
    assert argument.description == "This is a description"
    assert argument.type is str
    assert argument.default == "Patrick"


def test_annotated_argument_with_rename():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(
            self,
            arg: Annotated[
                str,
                strawberry.argument(name="argument"),
            ] = "Patrick",
        ) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    assert len(definition.fields[0].arguments) == 1

    argument = definition.fields[0].arguments[0]

    assert argument.python_name == "arg"
    assert argument.graphql_name == "argument"
    assert argument.type is str
    assert argument.description is None
    assert argument.default == "Patrick"


@pytest.mark.xfail(reason="Can't get field name from argument")
def test_multiple_annotated_arguments_exception():
    with pytest.raises(MultipleStrawberryArgumentsError) as error:

        @strawberry.field
        def name(
            argument: Annotated[
                str,
                strawberry.argument(description="This is a description"),
                strawberry.argument(description="Another description"),
            ],
        ) -> str:  # pragma: no cover
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
        def name(
            self, argument: Annotated[str, "Some other info"]
        ) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
    assert argument.description is None
    assert argument.type is str


def test_annotated_python_39():
    from typing import Annotated

    @strawberry.type
    class Query:
        @strawberry.field
        def name(
            self,
            argument: Annotated[
                str,
                strawberry.argument(description="This is a description"),
            ],
        ) -> str:  # pragma: no cover
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [argument] = definition.fields[0].arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
    assert argument.type is str
    assert argument.description == "This is a description"
    assert argument.type is str


@pytest.mark.raises_strawberry_exception(
    InvalidArgumentTypeError,
    'Argument "word" on field "add_word" cannot be of type "Union"',
)
def test_union_as_an_argument_type():
    @strawberry.type
    class Noun:
        text: str

    @strawberry.type
    class Verb:
        text: str

    Word = Annotated[Union[Noun, Verb], strawberry.argument("Word")]

    @strawberry.field
    def add_word(word: Word) -> bool:
        return True


@pytest.mark.raises_strawberry_exception(
    InvalidArgumentTypeError,
    'Argument "adjective" on field "add_adjective" cannot be of type "Interface"',
)
def test_interface_as_an_argument_type():
    @strawberry.interface
    class Adjective:
        text: str

    @strawberry.field
    def add_adjective(adjective: Adjective) -> bool:
        return True


@pytest.mark.raises_strawberry_exception(
    InvalidArgumentTypeError,
    (
        'Argument "adjective" on field "add_adjective_resolver" cannot be '
        'of type "Interface"'
    ),
)
def test_resolver_with_invalid_field_argument_type():
    @strawberry.interface
    class Adjective:
        text: str

    def add_adjective_resolver(adjective: Adjective) -> bool:  # pragma: no cover
        return True

    @strawberry.type
    class Mutation:
        add_adjective: bool = strawberry.field(resolver=add_adjective_resolver)


def test_unset_deprecation_warning():
    with pytest.deprecated_call():
        from strawberry.types.arguments import UNSET  # noqa: F401
    with pytest.deprecated_call():
        from strawberry.types.arguments import is_unset  # noqa: F401


def test_deprecated_unset():
    warning = "`is_unset` is deprecated use `value is UNSET` instead"

    with pytest.deprecated_call(match=warning):
        from strawberry.types.unset import is_unset

    with pytest.deprecated_call(match=warning):
        assert is_unset(UNSET)

    with pytest.deprecated_call(match=warning):
        assert not is_unset(None)

    with pytest.deprecated_call(match=warning):
        assert not is_unset(False)

    with pytest.deprecated_call(match=warning):
        assert not is_unset("hello world")
