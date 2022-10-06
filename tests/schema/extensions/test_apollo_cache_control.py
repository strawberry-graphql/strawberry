from __future__ import annotations

from typing import List

import strawberry
from strawberry.apollo.schema_directives import CacheControl, CacheControlScope
from strawberry.extensions import ApolloCacheControlExtension


def test_field_without_directive_should_set_max_age_0_and_no_scope():
    @strawberry.type
    class Person:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self, id: strawberry.ID) -> Person:
            return Person(id=id, name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[ApolloCacheControlExtension(calculate_http_headers=False)],
    )

    query = """
    query {
        person(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 0}


def test_top_level_scalar_without_directive_should_set_max_age_0_and_no_scope():
    @strawberry.type
    class Query:
        hi: str = strawberry.field(default="hi")

    schema = strawberry.Schema(
        query=Query,
        extensions=[ApolloCacheControlExtension(calculate_http_headers=False)],
    )

    query = """
    query {
       hi
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 0}


def test_field_without_directive_should_set_max_age_to_default_and_no_scope():
    @strawberry.type
    class Person:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self, id: strawberry.ID) -> Person:
            return Person(id=id, name="The Lord of the Rings")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        person(self(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 10}


def test_directive_specified_in_field_should_set_specified_max_age():
    @strawberry.type
    class Book:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=60)])
        def person(self, id: strawberry.ID) -> Book:
            return Book(id=id, name="Marco")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        person(self(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 60}


def test_directive_spceidfied_in_resolve_type_should_set_specified_max_age():
    @strawberry.type(directives=[CacheControl(max_age=60)])
    class Book:
        id: strawberry.ID
        title: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self, id: strawberry.ID) -> Book:
            return Book(id=id, title="The Lord of the Rings")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        book(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 60}


def test_directive_specified_in_resolve_type_extension_should_set_specified_max_age():
    @strawberry.type
    class Person:
        id: strawberry.ID
        name: str

    @strawberry.type(extend=True, name="Person", directives=[CacheControl(max_age=60)])
    class Dev:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self, id: strawberry.ID) -> Person:
            return Person(id=id, name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        person(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 60}


def test_max_age_0_specified_in_resolve_type_should_override_max_age():
    @strawberry.type(directives=[CacheControl(max_age=0)])
    class Person:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self, id: strawberry.ID) -> Person:
            return Person(id=id, name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        person(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 0}


def test_max_age_specified_in_field_should_override_resolve_type_max_age():
    @strawberry.type(directives=[CacheControl(max_age=60)])
    class Person:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=120)])
        def person(self, id: strawberry.ID) -> Person:
            return Person(id=id, name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        person(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 120}


def test_max_age_specified_in_field_should_override_resolve_type_keep_scope():
    @strawberry.type(
        directives=[CacheControl(max_age=60, scope=CacheControlScope.PRIVATE)]
    )
    class Person:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=120)])
        def person(self, id: strawberry.ID) -> Person:
            return Person(id=id, name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        person(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 120, "scope": "PRIVATE"}


def test_scope_specified_in_field_should_override_target_type_scope():
    @strawberry.type(
        directives=[CacheControl(max_age=60, scope=CacheControlScope.PUBLIC)]
    )
    class Person:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(
            directives=[CacheControl(max_age=120, scope=CacheControlScope.PRIVATE)]
        )
        def person(self, id: strawberry.ID) -> Person:
            return Person(id=id, name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False, default_max_age=10
            )
        ],
    )

    query = """
    query {
        person(id: 1) {
            name
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 120, "scope": "PRIVATE"}


def test_inheredit_max_age():
    @strawberry.type
    class Person:
        uncachedField: Person
        scalarField: str
        cachedField: str = strawberry.field(directives=[CacheControl(max_age=30)])

    @strawberry.type
    class PersonQuery:
        person: Person = strawberry.field(
            directives=[CacheControl(inheredit_max_age=True)]
        )
        persons: List[Person] = strawberry.field(
            directives=[CacheControl(inheredit_max_age=True)]
        )

    @strawberry.type
    class Query:
        top_level: PersonQuery = strawberry.field(
            directives=[CacheControl(max_age=1000)]
        )

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControlExtension(
                calculate_http_headers=False,
            )
        ],
    )

    query = """
    query {
      topLevel {
        droid {
          cachedField
        }
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 30, "scope": "PUBLIC"}
