from strawberry.types.fields.resolver import StrawberryResolver
import strawberry
from strawberry.decorator import make_strawberry_decorator


def test_basic_decorator():
    @make_strawberry_decorator
    def upper_case(resolver, **kwargs):
        result = resolver(**kwargs)
        return result.upper()

    @strawberry.type
    class Query:
        @strawberry.field
        @upper_case
        def greeting() -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { greeting }")

    assert not result.errors
    assert result.data == {"greeting": "HI"}


def test_decorator_with_arguments():
    def suffix(value):
        @make_strawberry_decorator
        def wrapper(resolver, **kwargs):
            result = resolver(**kwargs)
            return f"{result}{value}"

        return wrapper

    @strawberry.type
    class Query:
        @strawberry.field
        @suffix(" 👋")
        def greeting() -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { greeting }")

    assert not result.errors
    assert result.data == {"greeting": "hi 👋"}


def test_multiple_decorators():
    @make_strawberry_decorator
    def upper_case(resolver, **kwargs):
        result = resolver(**kwargs)
        return result.upper()

    def suffix(value):
        @make_strawberry_decorator
        def wrapper(resolver, **kwargs):
            result = resolver(**kwargs)
            return f"{result}{value}"

        return wrapper

    @strawberry.type
    class Query:
        @strawberry.field
        @suffix(" 👋")
        @upper_case
        def greeting() -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { greeting }")

    assert not result.errors
    assert result.data == {"greeting": "HI 👋"}


def test_decorator_with_graphql_arguments():
    @make_strawberry_decorator
    def upper_case(resolver, **kwargs):
        result = resolver(**kwargs)
        return result.upper()

    @strawberry.type
    class Query:
        @strawberry.field
        @upper_case
        def greeting(self, name: str) -> str:
            return f"hi {name}"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync('query { greeting(name: "everyone") }')

    assert not result.errors
    assert result.data == {"greeting": "HI EVERYONE"}


def test_decorator_modify_argument():
    def title_case_argument(argument_name):
        @make_strawberry_decorator
        def wrapped(resolver, **kwargs):
            kwargs[argument_name] = kwargs[argument_name].title()
            return resolver(**kwargs)

        return wrapped

    @strawberry.type
    class Query:
        @strawberry.field
        @title_case_argument("name")
        def greeting(self, name: str) -> str:
            return f"hi {name}"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync('query { greeting(name: "patrick") }')

    assert not result.errors
    assert result.data == {"greeting": "hi Patrick"}


def test_decorator_simple_field():
    @make_strawberry_decorator
    def upper_case(resolver, **kwargs):
        result = resolver(**kwargs)
        return result.upper()

    def suffix(value):
        @make_strawberry_decorator
        def wrapper(resolver, **kwargs):
            result = resolver(**kwargs)
            return f"{result}{value}"

        return wrapper

    @strawberry.type
    class Query:
        name: str = strawberry.field(decorators=[upper_case, suffix(" 👋")])

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
            query {
                name
            }
        """,
        root_value=Query(name="patrick"),
    )

    assert not result.errors
    assert result.data == {"name": "PATRICK 👋"}
