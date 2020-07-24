from typing import List, Optional

import strawberry


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
