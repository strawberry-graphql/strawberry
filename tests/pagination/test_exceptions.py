from typing import List

import pytest

import strawberry
from strawberry.pagination.exceptions import (
    ConnectionWrongAnnotationError,
    ConnectionWrongResolverAnnotationError,
)
from strawberry.pagination.fields import connection
from strawberry.pagination.types import Connection


@pytest.mark.raises_strawberry_exception(
    ConnectionWrongAnnotationError,
    match=(
        'Wrong annotation used on field "fruits_conn". '
        'It should be annotated with a "Connection" subclass.'
    ),
)
def test_raises_error_on_connection_missing_annotation():
    @strawberry.type
    class Fruit:
        pk: str

    @strawberry.type
    class Query:
        fruits_conn: List[Fruit] = connection()

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    ConnectionWrongAnnotationError,
    match=(
        'Wrong annotation used on field "custom_resolver". '
        'It should be annotated with a "Connection" subclass.'
    ),
)
def test_raises_error_on_connection_wrong_annotation():
    @strawberry.type
    class Fruit:
        pk: str

    @strawberry.type
    class Query:
        @connection(List[Fruit])  # type: ignore
        def custom_resolver(self) -> List[Fruit]: ...

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    ConnectionWrongResolverAnnotationError,
    match=(
        'Wrong annotation used on "custom_resolver" resolver. '
        "It should be return an iterable or async iterable object."
    ),
)
def test_raises_error_on_connection_resolver_wrong_annotation():
    @strawberry.type
    class Fruit:
        pk: str

    @strawberry.type
    class Query:
        @connection(Connection[Fruit])  # type: ignore
        def custom_resolver(self): ...

    strawberry.Schema(query=Query)
