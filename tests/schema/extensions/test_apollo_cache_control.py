import pytest

import strawberry
from strawberry.apollo.schema_directives import CacheControl, CacheControlScope
from strawberry.extensions import ApolloCacheControl


def test_field_without_directive_should_not_set_cache():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(
        query=Query,
        extensions=[ApolloCacheControl(calculate_http_headers=False)],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {}


def test_top_level_scalar_without_directive_should_not_set_cache():
    @strawberry.type
    class Query:
        hi: str = strawberry.field(default="hi")

    schema = strawberry.Schema(
        query=Query,
        extensions=[ApolloCacheControl(calculate_http_headers=False)],
    )

    result = schema.execute_sync("{ hi }")

    assert result.extensions == {}


def test_field_without_directive_should_set_max_age_to_default_and_public_scope():
    @strawberry.type
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person(name="Dino")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 10, "scope": "public"}


def test_directive_specified_in_field_should_set_specified_max_age():
    @strawberry.type
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=60)])
        def person(
            self,
        ) -> Person:
            return Person(name="Marco")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 60, "scope": "public"}


def test_directive_spceidfied_in_resolve_type_should_set_specified_max_age():
    @strawberry.type(directives=[CacheControl(max_age=60)])
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person(
            self,
        ) -> Person:
            return Person(name="Marcotte")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 60, "scope": "public"}


def test_directive_specified_in_resolve_type_extension_should_set_specified_max_age():
    @strawberry.type
    class Person:
        name: str = "Nick"

    @strawberry.type(extend=True, name="Person", directives=[CacheControl(max_age=60)])
    class Dev:
        role: str = "dev"

    @strawberry.type
    class Query:
        @strawberry.field
        def dev(self) -> Dev:
            return Dev()

    schema = strawberry.Schema(
        query=Query,
        types=[Dev],
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      dev {
        role
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 60, "scope": "public"}


def test_max_age_0_specified_in_resolve_type_should_override_default_max_age():
    @strawberry.type(directives=[CacheControl(max_age=0)])
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person(
            self,
        ) -> Person:
            return Person(name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {}


def test_max_age_specified_in_field_should_override_resolve_type_max_age():
    @strawberry.type(directives=[CacheControl(max_age=60)])
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=120)])
        def person(
            self,
        ) -> Person:
            return Person(name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 120, "scope": "public"}


def test_max_age_specified_in_field_should_override_resolver_type_keep_scope():
    @strawberry.type(
        directives=[CacheControl(max_age=60, scope=CacheControlScope.PRIVATE)]
    )
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=120)])
        def person(
            self,
        ) -> Person:
            return Person(name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 120, "scope": "private"}


def test_scope_specified_in_field_should_override_target_type_scope():
    @strawberry.type(
        directives=[CacheControl(max_age=60, scope=CacheControlScope.PUBLIC)]
    )
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(
            directives=[CacheControl(max_age=120, scope=CacheControlScope.PRIVATE)]
        )
        def person(
            self,
        ) -> Person:
            return Person(name="Ester")

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
        ],
    )

    query = """
    {
      person {
        name
      }
    }
    """

    result = schema.execute_sync(query)

    assert result.extensions == {"max_age": 120, "scope": "private"}


@pytest.mark.parametrize(
    "query, expected",
    [
        ("{ foo { defaultBar { scalar } } }", {}),
        ("{ foo { defaultBar { cachedScalar } } }", {}),
        ("{ foo { bar { scalar } } }", {"max_age": 5, "scope": "public"}),
        ("{ foo { bar { cachedScalar } } }", {"max_age": 2, "scope": "public"}),
    ],
)
def test_scalars_inherit_from_grandparents(query, expected):
    @strawberry.type
    class Bar:
        scalar: str
        cached_scalar: str = strawberry.field(directives=[CacheControl(max_age=2)])

    @strawberry.type
    class Foo:
        bar: Bar = strawberry.field(directives=[CacheControl(inheredit_max_age=True)])
        defaultBar: Bar

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=5)])
        def foo(
            self,
        ) -> Foo:
            return Foo(
                bar=Bar(scalar="scalar", cached_scalar="cached"),
                defaultBar=Bar(
                    scalar="default bar scalar", cached_scalar="default cached scalar"
                ),
            )

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(
                calculate_http_headers=False,
            )
        ],
    )

    result = schema.execute_sync(query)

    assert result.extensions == expected


def test_inherit_max_age_on_types():
    @strawberry.type(directives=[CacheControl(inheredit_max_age=True)])
    class Foo:
        bar: str

    @strawberry.type
    class TopLevel:
        foo: Foo

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=500)])
        def top_level(self) -> TopLevel:
            return TopLevel(foo=Foo(bar="ok"))

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(
                calculate_http_headers=False,
            )
        ],
    )

    result = schema.execute_sync("{ topLevel { foo { bar } } }")

    assert result.extensions == {"max_age": 500, "scope": "public"}


def test_inherit_max_age_on_types_keep_scope():
    @strawberry.type(
        directives=[
            CacheControl(inheredit_max_age=True, scope=CacheControlScope.PRIVATE)
        ]
    )
    class Foo:
        bar: str

    @strawberry.type
    class TopLevel:
        foo: Foo

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=500)])
        def top_level(self) -> TopLevel:
            return TopLevel(foo=Foo(bar="ok"))

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(
                calculate_http_headers=False,
            )
        ],
    )

    result = schema.execute_sync("{ topLevel { foo { bar } } }")

    assert result.extensions == {"max_age": 500, "scope": "private"}


def test_combine():
    @strawberry.type
    class Foo:
        bar: str = strawberry.field(directives=[CacheControl(max_age=5)])

    @strawberry.type
    class TopLevel:
        foo: Foo = strawberry.field(
            directives=[
                CacheControl(inheredit_max_age=True, scope=CacheControlScope.PRIVATE)
            ]
        )

    @strawberry.type
    class Query:
        @strawberry.field(directives=[CacheControl(max_age=500)])
        def top_level(self) -> TopLevel:
            return TopLevel(foo=Foo(bar="bar"))

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            ApolloCacheControl(
                calculate_http_headers=False,
            )
        ],
    )

    result = schema.execute_sync("{topLevel { foo { bar } } }")

    assert result.extensions == {"max_age": 5, "scope": "private"}
