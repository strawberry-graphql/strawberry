import typing
from enum import Enum

import pytest

import strawberry
from dataclasses import InitVar
from graphql import graphql, graphql_sync


def test_simple_type():
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["hello"] == "strawberry"


def test_init_var():
    @strawberry.type
    class Category:
        name: str
        id: InitVar[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self, info) -> Category:
            return Category(name="example", id="123")  # type:ignore

    schema = strawberry.Schema(query=Query)

    query = "{ category { name } }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["category"]["name"] == "example"


def test_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info) -> str:
            return "I'm a resolver"

    assert Query().hello(None) == "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["hello"] == "I'm a resolver"


@pytest.mark.asyncio
async def test_resolver_function():
    def function_resolver(root, info) -> str:
        return "I'm a function resolver"

    async def async_resolver(root, info) -> str:
        return "I'm an async resolver"

    def resolve_name(root, info) -> str:
        return root.name

    def resolve_say_hello(root, info, name: str) -> str:
        return f"Hello {name}"

    @strawberry.type
    class Query:
        hello: str = strawberry.field(resolver=function_resolver)
        hello_async: str = strawberry.field(resolver=async_resolver)
        get_name: str = strawberry.field(resolver=resolve_name)
        say_hello: str = strawberry.field(resolver=resolve_say_hello)

        name = "Patrick"

    schema = strawberry.Schema(query=Query)

    query = """{
        hello
        helloAsync
        getName
        sayHello(name: "Marco")
    }"""

    result = await graphql(schema, query, root_value=Query())

    assert not result.errors
    assert result.data["hello"] == "I'm a function resolver"
    assert result.data["helloAsync"] == "I'm an async resolver"
    assert result.data["getName"] == "Patrick"
    assert result.data["sayHello"] == "Hello Marco"


def test_resolvers_on_types():
    def function_resolver(root, info) -> str:
        return "I'm a function resolver"

    def function_resolver_with_params(root, info, x: str) -> str:
        return f"I'm {x}"

    @strawberry.type
    class Example:
        hello: str = strawberry.field(resolver=function_resolver)
        hello_with_params: str = strawberry.field(
            resolver=function_resolver_with_params
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self, info) -> Example:
            return Example()

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            hello
            helloWithParams(x: "abc")
        }
    }"""

    result = graphql_sync(schema, query, root_value=Query())

    assert not result.errors
    assert result.data["example"]["hello"] == "I'm a function resolver"
    assert result.data["example"]["helloWithParams"] == "I'm abc"


def test_nested_types():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info) -> User:
            # TODO: mypy is complaining about the next line, need to
            # understand how to fix it
            return User(name="Patrick")  # type:ignore

    assert Query().user(None) == User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["user"]["name"] == "Patrick"


def test_mutation():
    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(self, info) -> str:
            return "Hello!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = "mutation { say }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["say"] == "Hello!"


def test_mutation_with_input_type():
    @strawberry.input
    class SayInput:
        name: str

    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def say(self, info, input: SayInput) -> str:
            return f"Hello {input.name}!"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = 'mutation { say(input: { name: "Patrick"}) }'

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["say"] == "Hello Patrick!"


def test_does_camel_case_conversion():
    @strawberry.type
    class Query:
        hello_world: str = "strawberry"

        @strawberry.field
        def example(self, info, query_param: str) -> str:
            return query_param

    schema = strawberry.Schema(query=Query)

    query = """{
        helloWorld
        example(queryParam: "hi")
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["helloWorld"] == "strawberry"
    assert result.data["example"] == "hi"


def test_can_rename_fields():
    @strawberry.type
    class Query:
        hello_world: typing.Optional[str] = strawberry.field(name="hello")

        @strawberry.field(name="example1")
        def example(self, info, query_param: str) -> str:
            return query_param

    schema = strawberry.Schema(query=Query)

    query = """{
        hello
        example1(queryParam: "hi")
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["hello"] is None
    assert result.data["example1"] == "hi"


def test_type_description():
    @strawberry.type(description="Decorator argument description")
    class TypeA:
        a: str

    @strawberry.type
    class TypeB:
        """Docstring description"""

        a: str

    @strawberry.type(description="Decorator description overrides docstring")
    class TypeC:
        """Docstring description"""

        a: str

    @strawberry.type
    class Query:
        a: TypeA
        b: TypeB
        c: TypeC

    schema = strawberry.Schema(query=Query)

    query = """{
        __schema {
            types {
                name
                description
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors

    assert {
        "name": "TypeA",
        "description": "Decorator argument description",
    } in result.data["__schema"]["types"]

    assert {"name": "TypeB", "description": "Docstring description"} in result.data[
        "__schema"
    ]["types"]

    assert {
        "name": "TypeC",
        "description": "Decorator description overrides docstring",
    } in result.data["__schema"]["types"]


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

        @strawberry.field
        def d(self, info, id: int) -> str:
            """Example D"""
            return "I'm a resolver"

        @strawberry.field(description="Inline description")
        def e(self, info, id: int) -> str:
            """Doc string description"""
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

    result = graphql_sync(schema, query)

    assert not result.errors

    assert result.data["__type"]["fields"] == [
        {"name": "a", "description": "Example"},
        {"name": "b", "description": None},
        {"name": "c", "description": "Example C"},
        {"name": "d", "description": "Example D"},
        {"name": "e", "description": "Inline description"},
    ]


def test_enum_description():
    @strawberry.enum(description="We love ice-creams")
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.enum
    class PizzaType(Enum):
        """We also love pizza"""

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

    result = graphql_sync(schema, query)

    assert not result.errors

    assert result.data["iceCreamFlavour"]["description"] == "We love ice-creams"
    assert result.data["iceCreamFlavour"]["enumValues"] == [
        {"name": "VANILLA", "description": None},
        {"name": "STRAWBERRY", "description": None},
        {"name": "CHOCOLATE", "description": None},
    ]

    assert result.data["pizzas"]["description"] == "We also love pizza"


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

    schema = strawberry.Schema(query=Schema)

    query = "{ cheese, cake, friend, helloThisIs }"

    result = graphql_sync(schema, query)

    assert not result.errors

    assert result.data["cheese"] == "swiss"
    assert result.data["cake"] == "made_in_switzerland"
    assert result.data["friend"] == "food"
    assert result.data["helloThisIs"] == "patrick"
