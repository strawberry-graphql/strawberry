import dataclasses
from typing import List

import strawberry
from tests.objects.resolvers import any_list_resolver, bar_list_resolver


@strawberry.type
class Foo:
    name: str


def test_resolver_in_another_module():
    @strawberry.type
    class Query:
        foo: List["Foo"] = strawberry.field(resolver=any_list_resolver)

    [field] = dataclasses.fields(Query)
    assert field.type == List[Foo]
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { foo { name } }")
    assert result.data == {"foo": []}, result.errors


def test_resolver_and_type_in_another_module():
    @strawberry.type
    class Query:
        bar = strawberry.field(resolver=bar_list_resolver)

    [field] = dataclasses.fields(Query)
    from .resolvers import Bar

    assert field.type == List[Bar]
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { bar { name } }")
    assert result.data == {"bar": []}, result.errors
