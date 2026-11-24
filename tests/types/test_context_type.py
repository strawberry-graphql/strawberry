import textwrap
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Any

import pytest

import strawberry
from strawberry.directive import DirectiveLocation, DirectiveValue
from strawberry.exceptions import ConflictingArgumentsError
from strawberry.extensions import FieldExtension
from strawberry.utils.aio import aclosing


@dataclass
class MyContext:
    user_id: str


def test_context_parameter():
    @strawberry.type
    class Query:
        @strawberry.field
        def user_id(self, context: strawberry.Context[MyContext]) -> str:
            return context.user_id

    schema = strawberry.Schema(query=Query)

    expected = """\
        type Query {
          userId: String!
        }
    """
    assert textwrap.dedent(str(schema)).strip() == textwrap.dedent(expected).strip()

    result = schema.execute_sync("{ userId }", context_value=MyContext(user_id="1"))
    assert not result.errors
    assert result.data == {"userId": "1"}


@pytest.mark.asyncio
async def test_context_parameter_async_with_info_and_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        async def greeting(
            self,
            info: strawberry.Info,
            ctx: strawberry.Context[MyContext],
            name: str,
        ) -> str:
            assert ctx is info.context
            return f"Hello {name}, from {ctx.user_id}"

    schema = strawberry.Schema(query=Query)

    assert "greeting(name: String!): String!" in str(schema)

    result = await schema.execute(
        '{ greeting(name: "Ada") }', context_value=MyContext(user_id="2")
    )
    assert not result.errors
    assert result.data == {"greeting": "Hello Ada, from 2"}


class UpperCaseExtension(FieldExtension):
    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        return next_(source, info, **kwargs).upper()


@pytest.mark.parametrize("extensions", [[], [UpperCaseExtension()]])
def test_context_parameter_named_info(extensions):
    @strawberry.type
    class Query:
        @strawberry.field(extensions=extensions)
        def user_id(self, info: strawberry.Context[MyContext]) -> str:
            return f"user {info.user_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ userId }", context_value=MyContext(user_id="8"))
    assert not result.errors
    expected = "user 8" if not extensions else "USER 8"
    assert result.data == {"userId": expected}


def test_context_parameter_in_resolver_function():
    def get_user_id(context: strawberry.Context[MyContext]) -> str:
        return context.user_id

    @strawberry.type
    class Query:
        user_id: str = strawberry.field(resolver=get_user_id)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ userId }", context_value=MyContext(user_id="3"))
    assert not result.errors
    assert result.data == {"userId": "3"}


def test_context_parameter_with_parent():
    @strawberry.type
    class User:
        name: str

        @strawberry.field
        @staticmethod
        def greeting(
            parent: strawberry.Parent["User"],
            context: strawberry.Context[MyContext],
        ) -> str:
            return f"{parent.name} seen by {context.user_id}"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Ada")

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "{ user { greeting } }", context_value=MyContext(user_id="4")
    )
    assert not result.errors
    assert result.data == {"user": {"greeting": "Ada seen by 4"}}


@pytest.mark.asyncio
async def test_context_parameter_in_subscription():
    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def user_id(
            self, context: strawberry.Context[MyContext]
        ) -> AsyncGenerator[str, None]:
            yield context.user_id

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    async with aclosing(
        await schema.subscribe(
            "subscription { userId }", context_value=MyContext(user_id="5")
        )
    ) as sub_result:
        result = await sub_result.__anext__()

    assert not result.errors
    assert result.data == {"userId": "5"}


def test_context_parameter_in_directive():
    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def suffix_user_id(
        value: DirectiveValue[str], context: strawberry.Context[MyContext]
    ) -> str:
        return f"{value} ({context.user_id})"

    @strawberry.type
    class Query:
        @strawberry.field
        def greeting(self) -> str:
            return "Hello"

    schema = strawberry.Schema(query=Query, directives=[suffix_user_id])

    assert "directive @suffixUserId on FIELD" in str(schema)

    result = schema.execute_sync(
        "{ greeting @suffixUserId }", context_value=MyContext(user_id="6")
    )
    assert not result.errors
    assert result.data == {"greeting": "Hello (6)"}


@pytest.mark.raises_strawberry_exception(
    ConflictingArgumentsError,
    match=(
        "Arguments .* define conflicting resources. "
        "Only one of these arguments may be defined per resolver."
    ),
)
def test_multiple_context_parameters():
    def resolver(
        a: strawberry.Context[MyContext], b: strawberry.Context[MyContext]
    ) -> str:
        raise AssertionError("Unreachable code.")

    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=resolver)

    strawberry.Schema(query=Query)
