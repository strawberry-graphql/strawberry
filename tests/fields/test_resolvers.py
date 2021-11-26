import dataclasses
from typing import ClassVar

import pytest

import strawberry
from strawberry.exceptions import (
    MissingArgumentsAnnotationsError,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
)
from strawberry.types.fields.resolver import StrawberryResolver, UncallableResolverError


def test_resolver_as_argument():
    def get_name(self) -> str:
        return "Name"

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=get_name)

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
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

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == str
    assert definition.fields[0].base_resolver(None) == Query().name()


def test_staticmethod_resolver_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def name() -> str:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == str
    assert definition.fields[0].base_resolver() == Query.name()

    assert Query.name() == "Name"
    assert Query().name() == "Name"


def test_classmethod_resolver_fields():
    @strawberry.type
    class Query:
        my_val: ClassVar[str] = "thingy"

        @strawberry.field
        @classmethod
        def val(cls) -> str:
            return cls.my_val

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "val"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == str
    assert definition.fields[0].base_resolver() == Query.val()

    assert Query.val() == "thingy"
    assert Query().val() == "thingy"


def test_raises_error_when_return_annotation_missing():
    with pytest.raises(MissingReturnAnnotationError) as e:

        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self):
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
        def hello(self, query) -> str:
            return "I'm a resolver"

    assert e.value.args == (
        'Missing annotation for argument "query" in field "hello", '
        "did you forget to add it?",
    )

    with pytest.raises(MissingArgumentsAnnotationsError) as e:

        @strawberry.field
        def hello2(self, query, limit) -> str:
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


def test_raises_error_calling_uncallable_resolver():
    @staticmethod
    def static_func() -> int:
        ...

    resolver = StrawberryResolver(static_func)

    expected_error_message = (
        f"Attempted to call resolver {resolver} with uncallable function "
        f"{static_func}"
    )

    with pytest.raises(UncallableResolverError, match=expected_error_message):
        resolver()


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

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].base_resolver.wrapped_func == get_name

    assert definition.fields[1].python_name == "name_2"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].python_name == "name_2"
    assert definition.fields[1].type == str
    assert definition.fields[1].base_resolver.wrapped_func == get_name


def test_eq_resolvers():
    def get_name(self) -> str:
        return "Name"

    @strawberry.type
    class Query:
        a: int
        name: str = strawberry.field(resolver=get_name)
        name_2: str = strawberry.field(resolver=get_name)

    assert Query(1) == Query(1)
    assert Query(1) != Query(2)


def test_eq_fields():
    @strawberry.type
    class Query:
        a: int
        name: str = strawberry.field(name="name")

    assert Query(1, "name") == Query(1, "name")
    assert Query(1, "name") != Query(1, "not a name")


def test_with_resolver_fields():
    @strawberry.type
    class Query:
        a: int

        @strawberry.field
        def name(self) -> str:
            return "A"

    assert Query(1) == Query(1)
    assert Query(1) != Query(2)
