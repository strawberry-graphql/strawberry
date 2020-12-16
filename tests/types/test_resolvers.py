import dataclasses

import pytest

import strawberry
from strawberry.exceptions import (
    MissingArgumentsAnnotationsError,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
)


def test_resolver_as_argument():
    def get_name(self) -> str:
        return "Name"

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=get_name)

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].base_resolver.wrapped_func == get_name


def test_resolver_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self) -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].base_resolver(None) == Query().name()


def test_raises_error_when_return_annotation_missing():
    with pytest.raises(MissingReturnAnnotationError) as e:

        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self, info):
                return "I'm a resolver"

    assert e.value.args == (
        'Return annotation missing for field "hello", did you forget to add it?',
    )

    with pytest.raises(MissingReturnAnnotationError) as e:

        @strawberry.type
        class Query2:
            def adios(self):
                return -1

            goodbye = strawberry.field(resolver=adios)

    # TODO: Maybe we should say that the resolver needs the annotation?

    assert e.value.args == (
        'Return annotation missing for field "goodbye", did you forget to add it?',
    )


def test_raises_error_when_argument_annotation_missing():
    with pytest.raises(MissingArgumentsAnnotationsError) as e:

        @strawberry.field
        def hello(self, info, query) -> str:
            return "I'm a resolver"

    assert e.value.args == (
        'Missing annotation for argument "query" in field "hello", '
        "did you forget to add it?",
    )

    with pytest.raises(MissingArgumentsAnnotationsError) as e:

        @strawberry.field
        def hello2(self, info, query, limit) -> str:
            return "I'm a resolver"

    assert e.value.args == (
        'Missing annotation for arguments "limit" and "query" '
        'in field "hello2", did you forget to add it?',
    )


def test_raises_error_when_missing_annotation_and_resolver():
    with pytest.raises(MissingFieldAnnotationError) as e:

        @strawberry.type
        class Query:  # noqa: F841
            missing = strawberry.field(name="annotation")

    [message] = e.value.args
    assert message == (
        'Unable to determine the type of field "missing". Either annotate it '
        "directly, or provide a typed resolver using @strawberry.field."
    )


def test_raises_error_when_missing_type():
    """Test to make sure that if somehow a non-StrawberryField field is added to the cls
    without annotations it raises an exception. This would occur if someone manually
    uses dataclasses.field"""
    with pytest.raises(MissingFieldAnnotationError) as e:

        @strawberry.type
        class Query:  # noqa: F841
            missing = dataclasses.field()

    [message] = e.value.args
    assert message == (
        'Unable to determine the type of field "missing". Either annotate it '
        "directly, or provide a typed resolver using @strawberry.field."
    )


def test_can_reuse_resolver():
    def get_name(self) -> str:
        return "Name"

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=get_name)
        name_2: str = strawberry.field(resolver=get_name)

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].origin_name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].base_resolver.wrapped_func == get_name

    assert definition.fields[1].name == "name2"
    assert definition.fields[1].origin_name == "name_2"
    assert definition.fields[1].type == str
    assert definition.fields[1].base_resolver.wrapped_func == get_name
