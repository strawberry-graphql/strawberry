import typing
from typing import List

import pytest

import strawberry


def test_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info) -> str:
            return "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = schema.execute_sync(query)

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

    result = await schema.execute(query, root_value=Query())

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

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["example"]["hello"] == "I'm a function resolver"
    assert result.data["example"]["helloWithParams"] == "I'm abc"


def test_optional_info_and_root_params_function_resolver():
    def function_resolver() -> str:
        return "I'm a function resolver"

    def function_resolver_with_root(root) -> str:
        return root._example

    def function_resolver_with_params(x: str) -> str:
        return f"I'm {x}"

    @strawberry.type
    class Query:
        hello: str = strawberry.field(resolver=function_resolver)
        hello_with_root: str = strawberry.field(resolver=function_resolver_with_root)
        hello_with_params: str = strawberry.field(
            resolver=function_resolver_with_params
        )

        def __post_init__(self):
            self._example = "Example"

    schema = strawberry.Schema(query=Query)

    query = """{
        hello
        helloWithRoot
        helloWithParams(x: "abc")
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["hello"] == "I'm a function resolver"
    assert result.data["helloWithParams"] == "I'm abc"
    assert result.data["helloWithRoot"] == "Example"


def test_optional_info_and_root_params():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "I'm a function resolver"

        @strawberry.field
        def hello_with_params(self, x: str) -> str:
            return f"I'm {x}"

        @strawberry.field
        def uses_self(self) -> str:
            return f"I'm {self._example}"

        def __post_init__(self):
            self._example = "self"

    schema = strawberry.Schema(query=Query)

    query = """{
        hello
        helloWithParams(x: "abc")
        usesSelf
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["hello"] == "I'm a function resolver"
    assert result.data["helloWithParams"] == "I'm abc"
    assert result.data["usesSelf"] == "I'm self"


def test_only_info_function_resolvers():
    def function_resolver(info) -> str:
        return f"I'm a function resolver for {info.field_name}"

    def function_resolver_with_params(info, x: str) -> str:
        return f"I'm {x} for {info.field_name}"

    @strawberry.type
    class Query:
        hello: str = strawberry.field(resolver=function_resolver)
        hello_with_params: str = strawberry.field(
            resolver=function_resolver_with_params
        )

    schema = strawberry.Schema(query=Query)

    query = """{
        hello
        helloWithParams(x: "abc")
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["hello"] == "I'm a function resolver for hello"
    # TODO: in future, should we map names of info.field_name to the matching
    # dataclass field name?
    assert result.data["helloWithParams"] == "I'm abc for helloWithParams"


def test_classmethods_resolvers():
    @strawberry.type
    class User:
        name: str
        age: int

        @classmethod
        def get_users(cls) -> "List[User]":
            return [cls(name="Bob", age=10), cls(name="Nancy", age=30)]

    def get_users() -> typing.List[User]:
        return User.get_users()

    @strawberry.type
    class Query:
        users: typing.List[User] = strawberry.field(resolver=User.get_users)

    schema = strawberry.Schema(query=Query)

    query = "{ users { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"users": [{"name": "Bob"}, {"name": "Nancy"}]}
