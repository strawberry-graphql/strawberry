import textwrap
import typing
from dataclasses import InitVar, dataclass
from enum import Enum
from typing import Optional

import strawberry


def test_basic_schema():
    @strawberry.type
    class Query:
        example: str = "Example"

    schema = strawberry.Schema(query=Query)

    query = "{ example }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example"] == "Example"


def test_basic_schema_optional():
    @strawberry.type
    class Query:
        example: typing.Optional[str] = None

    schema = strawberry.Schema(query=Query)

    query = "{ example }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example"] is None


def test_basic_schema_types():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        user: typing.Optional[User] = None

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["user"] is None


def test_does_camel_case_conversion():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello_world(self, info, query_param: str) -> str:
            return query_param

    schema = strawberry.Schema(query=Query)

    query = """{
        helloWorld(queryParam: "hi")
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["helloWorld"] == "hi"


def test_can_rename_fields():
    @strawberry.type
    class Hello:
        value: typing.Optional[str] = strawberry.field(name="name")

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info) -> Hello:
            return Hello("hi")

        @strawberry.field(name="example1")
        def example(self, info, query_param: str) -> str:
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


def test_type_description():
    @strawberry.type(description="Decorator argument description")
    class TypeA:
        a: str

    @strawberry.type
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


def test_field_description():
    @strawberry.type
    class Query:
        a: str = strawberry.field(description="Example")

        @strawberry.field
        def b(self, info, id: int) -> str:
            return "I'm a resolver"

        @strawberry.field(description="Example C")
        def c(self, info, id: int) -> str:
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


def test_field_deprecated_reason():
    @strawberry.type
    class Query:
        a: str = strawberry.field(deprecation_reason="Deprecated A")

        @strawberry.field
        def b(self, info, id: int) -> str:
            return "I'm a resolver"

        @strawberry.field(deprecation_reason="Deprecated B")
        def c(self, info, id: int) -> str:
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


def test_field_deprecated_reason_subscription():
    @strawberry.type
    class Query:
        a: str

    @strawberry.type
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


def test_enum_description():
    @strawberry.enum(description="We love ice-creams")
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.enum
    class PizzaType(Enum):
        MARGHERITA = "margherita"

    @strawberry.type
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


def test_parent_class_fields_are_inherited():
    @strawberry.type
    class Parent:
        cheese: str = "swiss"

        @strawberry.field
        def friend(self, info) -> str:
            return "food"

    @strawberry.type
    class Schema(Parent):
        cake: str = "made_in_switzerland"

        @strawberry.field
        def hello_this_is(self, info) -> str:
            return "patrick"

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self, info) -> Schema:
            return Schema()

    schema = strawberry.Schema(query=Query)

    query = "{ example { cheese, cake, friend, helloThisIs } }"

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data["example"]["cheese"] == "swiss"
    assert result.data["example"]["cake"] == "made_in_switzerland"
    assert result.data["example"]["friend"] == "food"
    assert result.data["example"]["helloThisIs"] == "patrick"


def test_can_return_compatible_type():
    """Test that we can return a different type that has the same fields,
    for example when returning a Django Model."""

    @dataclass
    class Example:
        name: str

    @strawberry.type
    class Cheese:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def assortment(self, info) -> Cheese:
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


def test_init_var():
    @strawberry.type
    class Category:
        name: str
        id: InitVar[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self, info) -> Category:
            return Category(name="example", id="123")

    schema = strawberry.Schema(query=Query)

    query = "{ category { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["category"]["name"] == "example"


def test_nested_types():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info) -> User:
            return User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["name"] == "Patrick"


def test_multiple_fields_with_same_type():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        me: Optional[User] = None
        you: Optional[User] = None

    schema = strawberry.Schema(query=Query)

    query = "{ me { name } you { name } }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["me"] is None
    assert result.data["you"] is None


def test_str_magic_method_prints_schema_sdl():
    @strawberry.type
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
