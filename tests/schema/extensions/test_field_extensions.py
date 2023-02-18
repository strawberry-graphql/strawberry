import re
from typing import Any, Callable

import pytest

import strawberry
from strawberry.extensions.field_extension import FieldExtension
from strawberry.types import Info


def test_extension_argument_modification():
    class UpperCaseExtension(FieldExtension):
        def resolve(self, next: Callable[..., Any], source: Any, info: Info, **kwargs):
            result = next(source, info, **kwargs)
            return str(result).upper()

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
    class UpperCaseExtension(FieldExtension):
        def resolve(self, next: Callable[..., Any], source: Any, info: Info, **kwargs):
            result = next(source, info, **kwargs)
            return str(result).upper()

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


async def test_extension_result_modification_async():
    class UpperCaseExtension(FieldExtension):
        async def resolve_async(
            self, next: Callable[..., Any], source: Any, info: Info, **kwargs
        ):
            result = await next(source, info, **kwargs)
            return str(result).upper()

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[UpperCaseExtension()])
        async def string(self) -> str:
            return "This is a test!!"

    schema = strawberry.Schema(query=Query)
    query = "query { string }"

    result = await schema.execute(query)
    # The result should be lowercase because that is the last extension in the chain
    assert result.data["string"] == "THIS IS A TEST!!"


def test_fail_on_missing_sync_extensions():
    class LowerCaseExtension(FieldExtension):
        def resolve(self, next: Callable[..., Any], source: Any, info: Info, **kwargs):
            result = next(source, info, **kwargs)
            return str(result).lower()

    class UpperCaseExtension(FieldExtension):
        async def resolve_async(
            self, next: Callable[..., Any], source: Any, info: Info, **kwargs
        ):
            result = await next(source, info, **kwargs)
            return str(result).upper()

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[UpperCaseExtension(), LowerCaseExtension()])
        def string(self) -> str:
            return "This is a test!!"

    # LowerCaseExtension should work just fine because it's sync
    msg = (
        "Query fields cannot be resolved. Cannot add async-only extension(s) "
        "UpperCaseExtension to the sync resolver of Field string. "
        "Please add a resolve method to the extension."
    )
    with pytest.raises(TypeError, match=re.escape(msg)):
        strawberry.Schema(query=Query)


def test_fail_on_missing_async_extensions():
    class LowerCaseExtension(FieldExtension):
        def resolve(self, next: Callable[..., Any], source: Any, info: Info, **kwargs):
            result = next(source, info, **kwargs)
            return str(result).lower()

    class UpperCaseExtension(FieldExtension):
        async def resolve_async(
            self, next: Callable[..., Any], source: Any, info: Info, **kwargs
        ):
            result = await next(source, info, **kwargs)
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
        "Please add a resolve_async method to the extension."
    )
    with pytest.raises(TypeError, match=re.escape(msg)):
        strawberry.Schema(query=Query)


def test_extension_order_respected():
    class LowerCaseExtension(FieldExtension):
        def resolve(self, next: Callable[..., Any], source: Any, info: Info, **kwargs):
            result = next(source, info, **kwargs)
            return str(result).lower()

    class UpperCaseExtension(FieldExtension):
        def resolve(self, next: Callable[..., Any], source: Any, info: Info, **kwargs):
            result = next(source, info, **kwargs)
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
