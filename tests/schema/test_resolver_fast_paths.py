from collections.abc import AsyncGenerator
from operator import getitem
from typing import Any, Optional

import pytest

import strawberry
from strawberry.extensions import FieldExtension
from strawberry.schema.config import StrawberryConfig
from strawberry.types.field import StrawberryField


def test_basic_descriptor_is_read_once_per_alias():
    reads = []

    @strawberry.type
    class Query:
        value: int = strawberry.field(name="renamed")

    class Source:
        @property
        def value(self):
            reads.append("value")
            return len(reads)

    result = strawberry.Schema(Query).execute_sync(
        "{ first: renamed second: renamed }", root_value=Source()
    )
    assert result.errors is None
    assert result.data == {"first": 1, "second": 2}
    assert reads == ["value", "value"]


@pytest.mark.parametrize("default_resolver", [getattr, dict.get, getitem])
@pytest.mark.parametrize("missing", [False, True])
def test_basic_default_resolver_semantics(default_resolver, missing):
    calls = []

    def resolve(source, name):
        calls.append(name)
        return default_resolver(source, name)

    @strawberry.type
    class Query:
        value: Optional[int] = strawberry.field(name="renamed")

    source = {} if missing else {"value": 42}
    if default_resolver is getattr:
        source = type("Source", (), source)()

    result = strawberry.Schema(
        Query, config=StrawberryConfig(default_resolver=resolve)
    ).execute_sync("{ alias: renamed }", root_value=source)
    assert calls == ["value"]
    assert result.data == {"alias": None if missing else 42}
    if missing and default_resolver is not dict.get:
        assert len(result.errors) == 1
        assert result.errors[0].path == ["alias"]
        assert isinstance(
            result.errors[0].original_error,
            AttributeError if default_resolver is getattr else KeyError,
        )
    else:
        assert result.errors is None


def test_custom_field_get_result_keeps_info_and_fresh_arguments():
    calls = []

    class CustomField(StrawberryField):
        def get_result(self, source, info, args, kwargs):
            calls.append((self.python_name, info, args, kwargs))
            result = super().get_result(source, info, args, kwargs)
            args.append("mutated after call")
            kwargs["mutated"] = True
            return result + 1

    @strawberry.type
    class Query:
        basic: int = CustomField()

        @CustomField()
        def resolved(self) -> int:
            return self.basic

    result = strawberry.Schema(Query).execute_sync(
        "{ a: basic b: basic c: resolved d: resolved }", root_value=Query(basic=10)
    )
    assert result.errors is None
    assert result.data == dict.fromkeys("abcd", 11)
    assert [call[0] for call in calls] == ["basic", "basic", "resolved", "resolved"]
    assert calls[0][1] is calls[1][1] is None
    assert [call[1].path.key for call in calls[2:]] == ["c", "d"]
    assert len({id(call[2]) for call in calls}) == 4
    assert len({id(call[3]) for call in calls}) == 4


def test_custom_info_constructed_only_when_requested():
    constructed = []
    invoked = []

    class CustomInfo(strawberry.Info):
        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            constructed.append(self)

    @strawberry.type
    class Query:
        @strawberry.field
        def plain(self) -> int:
            invoked.append("plain")
            return 1

        @strawberry.field
        def requested(self, details: strawberry.Info) -> str:
            invoked.append("requested")
            assert isinstance(details, CustomInfo)
            assert details.context == {"key": 2}
            assert details.root_value is root
            assert details.python_name == "requested"
            return details.path.key

    root = Query()
    result = strawberry.Schema(
        Query, config=StrawberryConfig(info_class=CustomInfo)
    ).execute_sync(
        "{ plain alias: requested }", root_value=root, context_value={"key": 2}
    )
    assert result.errors is None
    assert result.data == {"plain": 1, "alias": "alias"}
    assert invoked == ["plain", "requested"]
    assert len(constructed) == 1


def test_extension_apply_and_resolve_keep_custom_field_behavior():
    calls = []

    class Extension(FieldExtension):
        def apply(self, field):
            calls.append("apply")

        def resolve(self, next_, source, info, **kwargs: Any):
            calls.append(("extension", info.path.key))
            return next_(source, info, **kwargs) + 1

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[Extension()])
        def value(self) -> int:
            calls.append("resolver")
            return 1

    result = strawberry.Schema(Query).execute_sync("{ alias: value }")
    assert result.errors is None
    assert result.data == {"alias": 2}
    assert calls == ["apply", ("extension", "alias"), "resolver"]


async def test_sync_returning_awaitable_and_async_resolver_called_once():
    calls = []

    async def result():
        calls.append("awaited")
        return 3

    @strawberry.type
    class Query:
        @strawberry.field
        def sync(self) -> int:
            calls.append("sync")
            return result()

        @strawberry.field
        async def async_(self) -> int:
            calls.append("async")
            return 4

    execution = await strawberry.Schema(Query).execute("{ sync async: async_ }")
    assert execution.errors is None
    assert execution.data == {"sync": 3, "async": 4}
    assert sorted(calls) == ["async", "awaited", "sync"]


async def test_subscription_invoked_once_and_payload_resolvers_once_per_event():
    calls = []

    @strawberry.type
    class Item:
        value: int

        @strawberry.field
        def doubled(self) -> int:
            calls.append("payload")
            return self.value * 2

    @strawberry.type
    class Query:
        value: int = 1

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def items(self) -> AsyncGenerator[Item, None]:
            calls.append("subscription")
            yield Item(value=1)
            yield Item(value=2)

    stream = await strawberry.Schema(Query, subscription=Subscription).subscribe(
        "subscription { items { value doubled } }"
    )
    results = [result async for result in stream]
    assert all(result.errors is None for result in results)
    assert [result.data for result in results] == [
        {"items": {"value": 1, "doubled": 2}},
        {"items": {"value": 2, "doubled": 4}},
    ]
    assert calls == ["subscription", "payload", "payload"]


@strawberry.input
class RecursiveInput:
    value: int
    children: list["RecursiveInput"] = strawberry.field(default_factory=list)


def test_recursive_input_keeps_generic_conversion():
    seen = []

    @strawberry.type
    class Query:
        @strawberry.field
        def total(self, item: RecursiveInput) -> int:
            seen.append(item)
            return item.value + sum(child.value for child in item.children)

    result = strawberry.Schema(Query).execute_sync(
        "{ total(item: {value: 1, children: [{value: 2}]}) }"
    )
    assert result.errors is None
    assert result.data == {"total": 3}
    assert isinstance(seen[0], RecursiveInput)
    assert isinstance(seen[0].children[0], RecursiveInput)


async def test_schema_middleware_can_forward_extra_keywords():
    from strawberry.extensions import SchemaExtension

    class Middleware(SchemaExtension):
        def resolve(self, next_, root, info, *args: Any, **kwargs: Any):
            return next_(root, info, *args, **kwargs, unused="ignored")

    @strawberry.type
    class Query:
        basic: int = 1

        @strawberry.field
        def resolved(self) -> int:
            return 2

        @strawberry.field
        async def async_resolved(self) -> int:
            return 3

    schema = strawberry.Schema(Query, extensions=[Middleware])
    result = schema.execute_sync("{ basic resolved }", root_value=Query())
    assert result.errors is None
    assert result.data == {"basic": 1, "resolved": 2}
    result = await schema.execute(
        "{ basic resolved asyncResolved }", root_value=Query()
    )
    assert result.errors is None
    assert result.data == {"basic": 1, "resolved": 2, "asyncResolved": 3}
