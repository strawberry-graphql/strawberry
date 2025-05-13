import re
from typing import Annotated, Any, Callable, Optional

import pytest

import strawberry
from strawberry.extensions.field_extension import (
    AsyncExtensionResolver,
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.schema.config import StrawberryConfig


class UpperCaseExtension(FieldExtension):
    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ):
        result = next_(source, info, **kwargs)
        return str(result).upper()


class LowerCaseExtension(FieldExtension):
    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ):
        result = next_(source, info, **kwargs)
        return str(result).lower()


class AsyncUpperCaseExtension(FieldExtension):
    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ):
        result = await next_(source, info, **kwargs)
        return str(result).upper()


class IdentityExtension(FieldExtension):
    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        return next_(source, info, **kwargs)

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        return await next_(source, info, **kwargs)


def test_extension_argument_modification():
    @strawberry.type
    class Query:
        @strawberry.field(extensions=[UpperCaseExtension()])
        def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = schema.execute_sync(query)
    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "THIS IS A TEST!!"


def test_extension_result_modification_sync():
    @strawberry.type
    class Query:
        @strawberry.field(extensions=[UpperCaseExtension()])
        def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = schema.execute_sync(query)
    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "THIS IS A TEST!!"


async def test_async_extension_on_sync_resolver():
    @strawberry.type
    class Query:
        @strawberry.field(extensions=[AsyncUpperCaseExtension()])
        def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = await schema.execute(query)
    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "THIS IS A TEST!!"


async def test_extension_result_modification_async():
    @strawberry.type
    class Query:
        @strawberry.field(extensions=[AsyncUpperCaseExtension()])
        async def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = await schema.execute(query)

    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "THIS IS A TEST!!"


def test_fail_cannot_use_async_before_sync_extensions():
    @strawberry.type
    class Query:
        @strawberry.field(extensions=[AsyncUpperCaseExtension(), LowerCaseExtension()])
        def string(self) -> str:
            return "This is a test!!"

    # LowerCaseExtension should work just fine because it's sync
    msg = (
        "Query fields cannot be resolved. Cannot mix async-only extension(s) "
        "AsyncUpperCaseExtension with sync-only extension(s) "
        "LowerCaseExtension on Field string. "
        "If possible try to change the execution order so that all sync-only "
        "extensions are executed first."
    )
    with pytest.raises(TypeError, match=re.escape(msg)):
        strawberry.Schema(query=Query)


async def test_can_use_sync_before_async_extensions():
    @strawberry.type
    class Query:
        @strawberry.field(extensions=[LowerCaseExtension(), AsyncUpperCaseExtension()])
        def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = await schema.execute(query)
    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "THIS IS A TEST!!"


async def test_can_use_sync_only_and_sync_before_async_extensions():
    """Use Sync - Sync + Async - Sync - Async possible."""

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[
                LowerCaseExtension(),
                IdentityExtension(),
                LowerCaseExtension(),
                AsyncUpperCaseExtension(),
            ]
        )
        def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = await schema.execute(query)
    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "THIS IS A TEST!!"


def test_fail_on_missing_async_extensions():
    class LowerCaseExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ):
            result = next_(source, info, **kwargs)
            return str(result).lower()

    class UpperCaseExtension(FieldExtension):
        async def resolve_async(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ):
            result = await next_(source, info, **kwargs)
            return str(result).upper()

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[UpperCaseExtension(), LowerCaseExtension()])
        async def string(self) -> str:
            return "This is a test!!"

    # UpperCaseExtension should work just fine because it's sync
    msg = (
        "Query fields cannot be resolved. Cannot add sync-only extension(s) "
        "LowerCaseExtension to the async resolver of Field string. "
        "Please add a resolve_async method to the extension(s)."
    )
    with pytest.raises(TypeError, match=re.escape(msg)):
        strawberry.Schema(query=Query)


def test_extension_order_respected():
    class LowerCaseExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ):
            result = next_(source, info, **kwargs)
            return str(result).lower()

    class UpperCaseExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ):
            result = next_(source, info, **kwargs)
            return str(result).upper()

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[UpperCaseExtension(), LowerCaseExtension()])
        def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = schema.execute_sync(query)
    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "this is a test!!"


def test_extension_argument_parsing():
    """Check that kwargs passed to field extensions have been converted into
    Strawberry types.
    """

    @strawberry.input
    class StringInput:
        some_input_value: str = strawberry.field(description="foo")

    field_kwargs = {}

    class CustomExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ):
            nonlocal field_kwargs
            field_kwargs = kwargs
            return next_(source, info, **kwargs)

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[CustomExtension()])
        def string(self, some_input: StringInput) -> str:
            return f"This is a test!! {some_input.some_input_value}"

    schema = strawberry.Schema(query=Query)
    query = 'query { string(someInput: { someInputValue: "foo" }) }'

    result = schema.execute_sync(query)
    assert result.data, result.errors
    assert result.data["string"] == "This is a test!! foo"

    assert isinstance(field_kwargs["some_input"], StringInput)
    input_value = field_kwargs["some_input"]
    assert input_value.some_input_value == "foo"
    assert input_value.__strawberry_definition__.is_input is True


def test_extension_mutate_arguments():
    class CustomExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ):
            kwargs["some_input"] += 10
            return next_(source, info, **kwargs)

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[CustomExtension()])
        def string(self, some_input: int) -> str:
            return f"This is a test!! {some_input}"

    schema = strawberry.Schema(query=Query)
    query = "query { string(someInput: 3) }"

    result = schema.execute_sync(query)
    assert result.data, result.errors
    assert result.data["string"] == "This is a test!! 13"


def test_extension_access_argument_metadata():
    field_kwargs = {}
    argument_metadata = {}

    class CustomExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ):
            nonlocal field_kwargs
            field_kwargs = kwargs

            for key in kwargs:
                argument_def = info.get_argument_definition(key)
                assert argument_def is not None
                argument_metadata[key] = argument_def.metadata

            return next_(source, info, **kwargs)

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[CustomExtension()])
        def string(
            self,
            some_input: Annotated[str, strawberry.argument(metadata={"test": "foo"})],
            another_input: Optional[str] = None,
        ) -> str:
            return f"This is a test!! {some_input}"

    schema = strawberry.Schema(query=Query)
    query = 'query { string(someInput: "foo") }'

    result = schema.execute_sync(query)
    assert result.data, result.errors
    assert result.data["string"] == "This is a test!! foo"

    assert isinstance(field_kwargs["some_input"], str)
    assert argument_metadata == {
        "some_input": {
            "test": "foo",
        },
        "another_input": {},
    }


def test_extension_has_custom_info_class():
    class CustomInfo(strawberry.Info):
        test: str = "foo"

    class CustomExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: CustomInfo,
            **kwargs: Any,
        ):
            assert isinstance(info, CustomInfo)
            # Explicitly check it's not Info.
            assert strawberry.Info in type(info).__bases__
            assert info.test == "foo"
            return next_(source, info, **kwargs)

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[CustomExtension()])
        def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(info_class=CustomInfo)
    )
    query = "query { string }"
    result = schema.execute_sync(query)
    assert result.data, result.errors
    assert result.data["string"] == "This is a test!!"
