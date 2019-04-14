import strawberry
from graphql import graphql_sync


def test_simple_type():
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["hello"] == "strawberry"


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
