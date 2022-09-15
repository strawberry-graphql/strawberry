import dataclasses
import re
from typing import ClassVar, List, no_type_check

import pytest

import strawberry
from strawberry.exceptions import (
    MissingArgumentsAnnotationsError,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
)
from strawberry.scalars import JSON
from strawberry.types.fields.resolver import (
    Signature,
    StrawberryResolver,
    UncallableResolverError,
)
from strawberry.types.info import Info


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
    @classmethod
    def class_func(cls) -> int:
        ...

    # Note that class_func is a raw classmethod object because it has not been bound
    # to a class at this point
    resolver = StrawberryResolver(class_func)

    expected_error_message = re.escape(
        f"Attempted to call resolver {resolver} with uncallable function "
        f"{class_func}"
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

    assert Query(a=1) == Query(a=1)
    assert Query(a=1) != Query(a=2)


def test_eq_fields():
    @strawberry.type
    class Query:
        a: int
        name: str = strawberry.field(name="name")

    assert Query(a=1, name="name") == Query(a=1, name="name")
    assert Query(a=1, name="name") != Query(a=1, name="not a name")


def test_with_resolver_fields():
    @strawberry.type
    class Query:
        a: int

        @strawberry.field
        def name(self) -> str:
            return "A"

    assert Query(a=1) == Query(a=1)
    assert Query(a=1) != Query(a=2)


def test_resolver_annotations():
    """Ensure only non-reserved annotations are returned."""

    def resolver_annotated_info(
        self, root, foo: str, bar: float, info: str, strawberry_info: Info
    ) -> str:
        return "Hello world"

    resolver = StrawberryResolver(resolver_annotated_info)

    expected_annotations = {"foo": str, "bar": float, "info": str, "return": str}
    assert resolver.annotations == expected_annotations

    # Sanity-check to ensure StrawberryArguments return the same annotations
    assert {
        **{
            arg.python_name: arg.type_annotation.resolve()  # type: ignore
            for arg in resolver.arguments
        },
        "return": str,
    }


@no_type_check
def test_resolver_with_unhashable_default():
    @strawberry.type
    class Query:
        @strawberry.field
        def field(
            self, x: List[str] = ["foo"], y: JSON = {"foo": 42}  # noqa: B006
        ) -> str:
            return f"{x} {y}"

    schema = strawberry.Schema(Query)
    result = schema.execute_sync("query { field }")
    assert result.data == {"field": "['foo'] {'foo': 42}"}
    assert not result.errors


@no_type_check
def test_parameter_hash_collision():
    """Ensure support for hashable defaults does not introduce collision."""

    def foo(x: str = "foo"):
        pass

    def bar(x: str = "bar"):
        pass

    foo_signature = Signature.from_callable(foo, follow_wrapped=True)
    bar_signature = Signature.from_callable(bar, follow_wrapped=True)

    foo_param = foo_signature.parameters["x"]
    bar_param = bar_signature.parameters["x"]

    # Ensure __eq__ still functions properly
    assert foo_param != bar_param

    # Ensure collision does not occur in hash-map and hash-tables. Colisions are
    # prevented by Python invoking __eq__ when two items have the same hash.
    parameters_map = {
        foo_param: "foo",
        bar_param: "bar",
    }
    parameters_set = {foo_param, bar_param}

    assert len(parameters_map) == 2
    assert len(parameters_set) == 2
