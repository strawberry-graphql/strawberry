import textwrap
import typing
from dataclasses import InitVar, dataclass
from enum import Enum
from typing import Optional

import pytest

import strawberry
from strawberry import ID
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
)
from strawberry.scalars import Base64
from strawberry.type import StrawberryList

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_raises_exception_with_unsupported_types(slots: bool):
    class SomeType:
        ...

    @strawberry.type(slots=slots)
    class Query:
        example: SomeType

    with pytest.raises(
        TypeError, match="Query fields cannot be resolved. Unexpected type '.*'"
    ):
        strawberry.Schema(query=Query)


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_basic_schema(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        example: str = "Example"

    schema = strawberry.Schema(query=Query)

    query = "{ example }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example"] == "Example"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_basic_schema_optional(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        example: typing.Optional[str] = None

    schema = strawberry.Schema(query=Query)

    query = "{ example }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example"] is None


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_basic_schema_types(slots: bool):
    @strawberry.type(slots=slots)
    class User:
        name: str

    @strawberry.type(slots=slots)
    class Query:
        user: typing.Optional[User] = None

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["user"] is None

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_does_camel_case_conversion(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        @strawberry.field
        def hello_world(self, query_param: str) -> str:
            return query_param

    schema = strawberry.Schema(query=Query)

    query = """{
        helloWorld(queryParam: "hi")
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["helloWorld"] == "hi"

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_can_rename_fields(slots: bool):
    @strawberry.type(slots=slots)
    class Hello:
        value: typing.Optional[str] = strawberry.field(name="name")

    @strawberry.type(slots=slots)
    class Query:
        @strawberry.field
        def hello(self) -> Hello:
            return Hello("hi")

        @strawberry.field(name="example1")
        def example(self, query_param: str) -> str:
            return query_param

    schema = strawberry.Schema(query=Query)

    query = """{
        hello { name }
        example1(queryParam: "hi")
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["hello"]["name"] == "hi"
    assert result.data["example1"] == "hi"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_type_description(slots: bool):
    @strawberry.type(description="Decorator argument description", slots=slots)
    class TypeA:
        a: str

    @strawberry.type(slots=slots)
    class Query:
        a: TypeA

    schema = strawberry.Schema(query=Query)

    query = """{
        __type(name: "TypeA") {
            name
            description
        }
    }"""

    result = schema.execute_sync(query)
    assert not result.errors

    assert result.data["__type"] == {
        "name": "TypeA",
        "description": "Decorator argument description",
    }

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_field_description(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        a: str = strawberry.field(description="Example")

        @strawberry.field
        def b(self, id: int) -> str:
            return "I'm a resolver"

        @strawberry.field(description="Example C")
        def c(self, id: int) -> str:
            return "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = """{
        __type(name: "Query") {
            fields {
                name
                description
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data["__type"]["fields"] == [
        {"name": "a", "description": "Example"},
        {"name": "b", "description": None},
        {"name": "c", "description": "Example C"},
    ]

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_field_deprecated_reason(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        a: str = strawberry.field(deprecation_reason="Deprecated A")

        @strawberry.field
        def b(self, id: int) -> str:
            return "I'm a resolver"

        @strawberry.field(deprecation_reason="Deprecated B")
        def c(self, id: int) -> str:
            return "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = """{
        __type(name: "Query") {
            fields(includeDeprecated: true) {
                name
                deprecationReason
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["__type"]["fields"] == [
        {"name": "a", "deprecationReason": "Deprecated A"},
        {"name": "b", "deprecationReason": None},
        {"name": "c", "deprecationReason": "Deprecated B"},
    ]

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_field_deprecated_reason_subscription(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        a: str

    @strawberry.type(slots=slots)
    class Subscription:
        @strawberry.subscription(deprecation_reason="Deprecated A")
        def a(self) -> str:
            return "A"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = """{
        __type(name: "Subscription") {
            fields(includeDeprecated: true) {
                name
                deprecationReason
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["__type"]["fields"] == [
        {"name": "a", "deprecationReason": "Deprecated A"},
    ]


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_enum_description(slots: bool):
    @strawberry.enum(description="We love ice-creams")
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.enum
    class PizzaType(Enum):
        MARGHERITA = "margherita"

    @strawberry.type(slots=slots)
    class Query:
        favorite_ice_cream: IceCreamFlavour = IceCreamFlavour.STRAWBERRY
        pizza: PizzaType = PizzaType.MARGHERITA

    schema = strawberry.Schema(query=Query)

    query = """{
        iceCreamFlavour: __type(name: "IceCreamFlavour") {
            description
            enumValues {
                name
                description
            }
        }
        pizzas: __type(name: "PizzaType") {
            description
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data["iceCreamFlavour"]["description"] == "We love ice-creams"
    assert result.data["iceCreamFlavour"]["enumValues"] == [
        {"name": "VANILLA", "description": None},
        {"name": "STRAWBERRY", "description": None},
        {"name": "CHOCOLATE", "description": None},
    ]

    assert result.data["pizzas"]["description"] is None

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_parent_class_fields_are_inherited(slots: bool):
    @strawberry.type(slots=slots)
    class Parent:
        cheese: str = "swiss"

        @strawberry.field
        def friend(self) -> str:
            return "food"

    @strawberry.type(slots=slots)
    class Schema(Parent):
        cake: str = "made_in_switzerland"

        @strawberry.field
        def hello_this_is(self) -> str:
            return "patrick"

    @strawberry.type(slots=slots)
    class Query:
        @strawberry.field
        def example(self) -> Schema:
            return Schema()

    schema = strawberry.Schema(query=Query)

    query = "{ example { cheese, cake, friend, helloThisIs } }"

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data["example"]["cheese"] == "swiss"
    assert result.data["example"]["cake"] == "made_in_switzerland"
    assert result.data["example"]["friend"] == "food"
    assert result.data["example"]["helloThisIs"] == "patrick"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_can_return_compatible_type(slots: bool):
    """Test that we can return a different type that has the same fields,
    for example when returning a Django Model."""

    @dataclass(slots=slots)
    class Example:
        name: str

    @strawberry.type(slots=slots)
    class Cheese:
        name: str

    @strawberry.type(slots=slots)
    class Query:
        @strawberry.field
        def assortment(self) -> Cheese:
            return Example(name="Asiago")  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = """{
        assortment {
            name
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["assortment"]["name"] == "Asiago"

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_init_var(slots: bool):
    @strawberry.type(slots=slots)
    class Category:
        name: str
        id: InitVar[str]

    @strawberry.type(slots=slots)
    class Query:
        @strawberry.field
        def category(self) -> Category:
            return Category(name="example", id="123")

    schema = strawberry.Schema(query=Query)

    query = "{ category { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["category"]["name"] == "example"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_nested_types(slots: bool):
    @strawberry.type(slots=slots)
    class User:
        name: str

    @strawberry.type(slots=slots)
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["name"] == "Patrick"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_multiple_fields_with_same_type(slots: bool):
    @strawberry.type(slots=slots)
    class User:
        name: str

    @strawberry.type(slots=slots)
    class Query:
        me: Optional[User] = None
        you: Optional[User] = None

    schema = strawberry.Schema(query=Query)

    query = "{ me { name } you { name } }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["me"] is None
    assert result.data["you"] is None

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_str_magic_method_prints_schema_sdl(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        exampleBool: bool
        exampleStr: str = "Example"
        exampleInt: int = 1

    schema = strawberry.Schema(query=Query)
    expected = """
    type Query {
      exampleBool: Boolean!
      exampleStr: String!
      exampleInt: Int!
    }
    """
    assert str(schema) == textwrap.dedent(expected).strip()
    assert "<strawberry.schema.schema.Schema object" in repr(
        schema
    ), "Repr should not be affected"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_field_with_default(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        a: str = strawberry.field(default="Example")

    schema = strawberry.Schema(query=Query)

    query = "{ a }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {"a": "Example"}


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_field_with_resolver_default(slots: bool):
    with pytest.raises(FieldWithResolverAndDefaultValueError):

        @strawberry.type(slots=slots)
        class Query:
            @strawberry.field(default="Example C")
            def c(self) -> str:
                return "I'm a resolver"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_field_with_separate_resolver_default(slots: bool):
    with pytest.raises(FieldWithResolverAndDefaultValueError):

        def test_resolver() -> str:
            return "I'm a resolver"

        @strawberry.type(slots=slots)
        class Query:
            c: str = strawberry.field(default="Example C", resolver=test_resolver)

@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_field_with_resolver_default_factory(slots: bool):
    with pytest.raises(FieldWithResolverAndDefaultFactoryError):

        @strawberry.type(slots=slots)
        class Query:
            @strawberry.field(default_factory=lambda: "Example C")
            def c(self) -> str:
                return "I'm a resolver"


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_with_types(slots: bool):
    # Ensures Schema(types=[...]) works with all data types
    @strawberry.type(slots=slots)
    class Type:
        foo: int

    @strawberry.interface
    class Interface:
        foo: int

    @strawberry.input
    class Input:
        foo: int

    @strawberry.type(slots=slots)
    class Query:
        foo: int

    schema = strawberry.Schema(
        query=Query, types=[Type, Interface, Input, Base64, ID, str, int]
    )
    expected = '''
        """
        Represents binary data as Base64-encoded strings, using the standard alphabet.
        """
        scalar Base64 @specifiedBy(url: "https://datatracker.ietf.org/doc/html/rfc4648.html#section-4")

        input Input {
          foo: Int!
        }

        interface Interface {
          foo: Int!
        }

        type Query {
          foo: Int!
        }

        type Type {
          foo: Int!
        }
    '''  # noqa: E501

    assert str(schema) == textwrap.dedent(expected).strip()


@pytest.mark.parametrize(
    "slots",
    (
        True,
        False,
    ),
)
def test_with_types_non_named(slots: bool):
    @strawberry.type(slots=slots)
    class Query:
        foo: int

    with pytest.raises(TypeError, match=r"\[Int!\] is not a named GraphQL Type"):
        strawberry.Schema(query=Query, types=[StrawberryList(int)])
