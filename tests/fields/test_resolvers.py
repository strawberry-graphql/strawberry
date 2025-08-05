import dataclasses
import textwrap
import types
from typing import Any, ClassVar, no_type_check

import pytest

import strawberry
from strawberry.exceptions import (
    MissingArgumentsAnnotationsError,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
)
from strawberry.parent import Parent
from strawberry.scalars import JSON
from strawberry.types.fields.resolver import (
    Signature,
    StrawberryResolver,
    UncallableResolverError,
)


def test_resolver_as_argument():
    def get_name(self) -> str:
        return "Name"

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=get_name)

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type is str
    assert definition.fields[0].base_resolver.wrapped_func == get_name


def test_resolver_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self) -> str:
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type is str
    assert definition.fields[0].base_resolver(None) == Query().name()


def test_staticmethod_resolver_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def name() -> str:
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type is str
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

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "val"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type is str
    assert definition.fields[0].base_resolver() == Query.val()

    assert Query.val() == "thingy"
    assert Query().val() == "thingy"


@pytest.mark.raises_strawberry_exception(
    MissingReturnAnnotationError,
    match='Return annotation missing for field "hello", did you forget to add it?',
)
def test_raises_error_when_return_annotation_missing():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self):
            return "I'm a resolver"


@pytest.mark.raises_strawberry_exception(
    MissingReturnAnnotationError,
    match='Return annotation missing for field "hello", did you forget to add it?',
)
def test_raises_error_when_return_annotation_missing_async_function():
    @strawberry.type
    class Query:
        @strawberry.field
        async def hello(self):
            return "I'm a resolver"


@pytest.mark.raises_strawberry_exception(
    MissingReturnAnnotationError,
    match='Return annotation missing for field "goodbye", did you forget to add it?',
)
def test_raises_error_when_return_annotation_missing_resolver():
    @strawberry.type
    class Query2:
        def adios(self):
            return -1

        goodbye = strawberry.field(resolver=adios)


@pytest.mark.raises_strawberry_exception(
    MissingArgumentsAnnotationsError,
    match=(
        'Missing annotation for argument "query" in field "hello", '
        "did you forget to add it?"
    ),
)
def test_raises_error_when_argument_annotation_missing():
    @strawberry.field
    def hello(self, query) -> str:
        return "I'm a resolver"


@pytest.mark.raises_strawberry_exception(
    MissingArgumentsAnnotationsError,
    match=(
        'Missing annotation for arguments "query" and "limit" '
        'in field "hello", did you forget to add it?'
    ),
)
def test_raises_error_when_argument_annotation_missing_multiple_fields():
    @strawberry.field
    def hello(self, query, limit) -> str:
        return "I'm a resolver"


@pytest.mark.raises_strawberry_exception(
    MissingArgumentsAnnotationsError,
    match=(
        'Missing annotation for argument "query" '
        'in field "hello", did you forget to add it?'
    ),
)
def test_raises_error_when_argument_annotation_missing_multiple_lines():
    @strawberry.field
    def hello(
        self,
        query,
    ) -> str:
        return "I'm a resolver"


@pytest.mark.raises_strawberry_exception(
    MissingArgumentsAnnotationsError,
    match=(
        'Missing annotation for argument "query" '
        'in field "hello", did you forget to add it?'
    ),
)
def test_raises_error_when_argument_annotation_missing_default_value():
    @strawberry.field
    def hello(
        self,
        query="this is a default value",
    ) -> str:
        return "I'm a resolver"


@pytest.mark.raises_strawberry_exception(
    MissingFieldAnnotationError,
    match=(
        'Unable to determine the type of field "missing". '
        "Either annotate it directly, or provide a typed resolver "
        "using @strawberry.field."
    ),
)
def test_raises_error_when_missing_annotation_and_resolver():
    @strawberry.type
    class Query:
        missing = strawberry.field(name="annotation")


@pytest.mark.raises_strawberry_exception(
    MissingFieldAnnotationError,
    match=(
        'Unable to determine the type of field "missing". Either annotate it '
        "directly, or provide a typed resolver using @strawberry.field."
    ),
)
def test_raises_error_when_missing_type():
    """Test to make sure that if somehow a non-StrawberryField field is added to the cls
    without annotations it raises an exception. This would occur if someone manually
    uses dataclasses.field
    """

    @strawberry.type
    class Query:
        missing = dataclasses.field()


@pytest.mark.raises_strawberry_exception(
    MissingFieldAnnotationError,
    match=(
        'Unable to determine the type of field "missing". Either annotate it '
        "directly, or provide a typed resolver using @strawberry.field."
    ),
)
def test_raises_error_when_missing_type_on_dynamic_class():
    # this test if for making sure the code that finds the exception source
    # doesn't crash with dynamic code

    namespace = {"missing": dataclasses.field()}

    strawberry.type(types.new_class("Query", (), {}, lambda ns: ns.update(namespace)))


@pytest.mark.raises_strawberry_exception(
    MissingFieldAnnotationError,
    match=(
        'Unable to determine the type of field "banana". Either annotate it '
        "directly, or provide a typed resolver using @strawberry.field."
    ),
)
def test_raises_error_when_missing_type_on_longish_class():
    @strawberry.type
    class Query:
        field_1: str = strawberry.field(name="field_1")
        field_2: str = strawberry.field(name="field_2")
        field_3: str = strawberry.field(name="field_3")
        field_4: str = strawberry.field(name="field_4")
        field_5: str = strawberry.field(name="field_5")
        field_6: str = strawberry.field(name="field_6")
        field_7: str = strawberry.field(name="field_7")
        field_8: str = strawberry.field(name="field_8")
        field_9: str = strawberry.field(name="field_9")
        banana = strawberry.field(name="banana")
        field_10: str = strawberry.field(name="field_10")
        field_11: str = strawberry.field(name="field_11")
        field_12: str = strawberry.field(name="field_12")
        field_13: str = strawberry.field(name="field_13")
        field_14: str = strawberry.field(name="field_14")
        field_15: str = strawberry.field(name="field_15")
        field_16: str = strawberry.field(name="field_16")
        field_17: str = strawberry.field(name="field_17")
        field_18: str = strawberry.field(name="field_18")
        field_19: str = strawberry.field(name="field_19")


def test_raises_error_calling_uncallable_resolver():
    @classmethod  # type: ignore
    def class_func(cls) -> int: ...

    # Note that class_func is a raw classmethod object because it has not been bound
    # to a class at this point
    resolver = StrawberryResolver(class_func)

    with pytest.raises(
        UncallableResolverError,
        match="Attempted to call resolver (.*) with uncallable function (.*)",
    ):
        resolver()


def test_can_reuse_resolver():
    def get_name(self) -> str:
        return "Name"

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=get_name)
        name_2: str = strawberry.field(resolver=get_name)

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].type is str
    assert definition.fields[0].base_resolver.wrapped_func == get_name

    assert definition.fields[1].python_name == "name_2"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].python_name == "name_2"
    assert definition.fields[1].type is str
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


def root_and_info(
    root,
    foo: str,
    bar: float,
    info: str,
    strawberry_info: strawberry.Info,
) -> str:
    raise AssertionError("Unreachable code.")


def self_and_info(
    self,
    foo: str,
    bar: float,
    info: str,
    strawberry_info: strawberry.Info,
) -> str:
    raise AssertionError("Unreachable code.")


def parent_and_info(
    parent: Parent[str],
    foo: str,
    bar: float,
    info: str,
    strawberry_info: strawberry.Info,
) -> str:
    raise AssertionError("Unreachable code.")


@pytest.mark.parametrize(
    "resolver_func",
    [
        pytest.param(self_and_info),
        pytest.param(root_and_info),
        pytest.param(parent_and_info),
    ],
)
def test_resolver_annotations(resolver_func):
    """Ensure only non-reserved annotations are returned."""
    resolver = StrawberryResolver(resolver_func)

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
        def field(self, x: list[str] = ["foo"], y: JSON = {"foo": 42}) -> str:  # noqa: B006
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


def test_annotation_using_parent_annotation():
    @strawberry.type
    class FruitType:
        name: str

        @strawberry.field
        @staticmethod
        def name_from_parent(parent: strawberry.Parent[Any]) -> str:
            return f"Using 'parent': {parent.name}"

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def fruit() -> FruitType:
            return FruitType(name="Strawberry")

    schema = strawberry.Schema(query=Query)
    expected = """\
      type FruitType {
        name: String!
        nameFromParent: String!
      }

      type Query {
        fruit: FruitType!
      }
    """

    assert textwrap.dedent(str(schema)) == textwrap.dedent(expected).strip()

    result = schema.execute_sync("query { fruit { name nameFromParent } }")
    assert result.data == {
        "fruit": {
            "name": "Strawberry",
            "nameFromParent": "Using 'parent': Strawberry",
        }
    }


def test_annotation_using_parent_annotation_but_named_root():
    @strawberry.type
    class FruitType:
        name: str

        @strawberry.field
        @staticmethod
        def name_from_parent(root: strawberry.Parent[Any]) -> str:
            return f"Using 'root': {root.name}"

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def fruit() -> FruitType:
            return FruitType(name="Strawberry")

    schema = strawberry.Schema(query=Query)
    expected = """\
      type FruitType {
        name: String!
        nameFromParent: String!
      }

      type Query {
        fruit: FruitType!
      }
    """

    assert textwrap.dedent(str(schema)) == textwrap.dedent(expected).strip()

    result = schema.execute_sync("query { fruit { name nameFromParent } }")
    assert result.data == {
        "fruit": {
            "name": "Strawberry",
            "nameFromParent": "Using 'root': Strawberry",
        }
    }
