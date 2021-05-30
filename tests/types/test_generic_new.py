from typing import Generic, TypeVar

import strawberry
from strawberry.schema.schema_converter import GraphQLCoreConverter


class TestGeneric:

    def test_simple_generic(self):
        T = TypeVar("T")

        @strawberry.type
        class MyType(Generic[T]):
            some_field: T

        @strawberry.type
        class Query:
            my_field: MyType[int]

        query_type = GraphQLCoreConverter().from_object(Query)
        print(1)
