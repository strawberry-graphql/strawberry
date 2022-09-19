# type: ignore
import typing
from typing import Any, List, Type, TypeVar

import pytest

import strawberry
from strawberry.types.info import Info


def test_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["hello"] == "I'm a resolver"


@pytest.mark.asyncio
async def test_resolver_function():
    def function_resolver(root) -> str:
        return "I'm a function resolver"

    async def async_resolver(root) -> str:
        return "I'm an async resolver"

    def resolve_name(root) -> str:
        return root.name

    def resolve_say_hello(root, name: str) -> str:
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
    def function_resolver(root) -> str:
        return "I'm a function resolver"

    def function_resolver_with_params(root, x: str) -> str:
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
        def example(self) -> Example:
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
    def function_resolver(info: Info) -> str:
        return f"I'm a function resolver for {info.field_name}"

    def function_resolver_with_params(info: Info, x: str) -> str:
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


def test_classmethod_resolvers():
    global User

    @strawberry.type
    class User:
        name: str
        age: int

        @classmethod
        def get_users(cls) -> "List[User]":
            return [cls(name="Bob", age=10), cls(name="Nancy", age=30)]

    @strawberry.type
    class Query:
        users: typing.List[User] = strawberry.field(resolver=User.get_users)

    schema = strawberry.Schema(query=Query)

    query = "{ users { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"users": [{"name": "Bob"}, {"name": "Nancy"}]}

    del User


def test_staticmethod_resolvers():
    class Alphabet:
        @staticmethod
        def get_letters() -> List[str]:
            return ["a", "b", "c"]

    @strawberry.type
    class Query:
        letters: List[str] = strawberry.field(resolver=Alphabet.get_letters)

    schema = strawberry.Schema(query=Query)

    query = "{ letters }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"letters": ["a", "b", "c"]}


def test_lambda_resolvers():
    @strawberry.type
    class Query:
        letter: str = strawberry.field(resolver=lambda: "λ")

    schema = strawberry.Schema(query=Query)

    query = "{ letter }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"letter": "λ"}


def test_bounded_instance_method_resolvers():
    class CoolClass:
        def method(self):
            _ = self
            return "something"

    instance = CoolClass()

    @strawberry.type
    class Query:
        blah: str = strawberry.field(resolver=instance.method)

    schema = strawberry.Schema(query=Query)

    query = "{ blah }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"blah": "something"}


def test_extending_type():
    def name_resolver(id: strawberry.ID) -> str:
        return "Name"

    def name_2_resolver(id: strawberry.ID) -> str:
        return "Name 2"

    @strawberry.type
    class NameQuery:
        name: str = strawberry.field(permission_classes=[], resolver=name_resolver)

    @strawberry.type
    class ExampleQuery:
        name_2: str = strawberry.field(permission_classes=[], resolver=name_2_resolver)

    @strawberry.type
    class RootQuery(NameQuery, ExampleQuery):
        pass

    schema = strawberry.Schema(query=RootQuery)

    query = '{ name(id: "abc"), name2(id: "abc") }'

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"name": "Name", "name2": "Name 2"}


@pytest.mark.asyncio
async def test_async_list_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        async def best_flavours(self) -> List[str]:
            return ["strawberry", "pistachio"]

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavours }"

    result = await schema.execute(query, root_value=Query())

    assert not result.errors
    assert result.data["bestFlavours"] == ["strawberry", "pistachio"]


def test_can_use_source_as_argument_name():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, source: str) -> str:
            return f"I'm a resolver for {source}"

    schema = strawberry.Schema(query=Query)

    query = '{ hello(source: "🍓") }'

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["hello"] == "I'm a resolver for 🍓"


def test_typed_resolver_factory():
    @strawberry.type
    class AType:
        some: int

    T = TypeVar("T")

    def resolver_factory(strawberry_type: Type[T]):
        def resolver() -> T:
            return strawberry_type(some=1)

        return resolver

    @strawberry.type
    class Query:
        a_type: AType = strawberry.field(resolver_factory(AType))

    strawberry.Schema(query=Query)

    schema = strawberry.Schema(query=Query)

    query = "{ aType { some } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"aType": {"some": 1}}


def name_based_info(info, icon: str) -> str:
    return f"I'm a resolver for {icon} {info.field_name}"


def type_based_info(info: Info, icon: str) -> str:
    return f"I'm a resolver for {icon} {info.field_name}"


def generic_type_based_info(icon: str, info: Info[Any, Any]) -> str:
    return f"I'm a resolver for {icon} {info.field_name}"


def arbitrarily_named_info(icon: str, info_argument: Info) -> str:
    return f"I'm a resolver for {icon} {info_argument.field_name}"


@pytest.mark.parametrize(
    "resolver",
    (
        pytest.param(name_based_info),
        pytest.param(type_based_info),
        pytest.param(generic_type_based_info),
        pytest.param(arbitrarily_named_info),
    ),
)
def test_info_argument(resolver):
    @strawberry.type
    class ResolverGreeting:
        hello: str = strawberry.field(resolver=resolver)

    schema = strawberry.Schema(query=ResolverGreeting)
    result = schema.execute_sync('{ hello(icon: "🍓") }')

    assert not result.errors
    assert result.data["hello"] == "I'm a resolver for 🍓 hello"


def test_name_based_info_is_deprecated():

    with pytest.deprecated_call(match=r"Argument name-based matching of 'info'"):

        @strawberry.type
        class Query:
            @strawberry.field
            def foo(info: Any) -> str:
                ...

        strawberry.Schema(query=Query)
