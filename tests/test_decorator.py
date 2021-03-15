import functools
from functools import wraps

import strawberry
from strawberry.types import Info


def test_basic_decorator():
    def upper_case(resolver):
        @wraps(resolver)
        def wrapped(*args, **kwargs):
            return resolver(*args, **kwargs).upper()

        return wrapped

    @strawberry.type
    class Query:
        @strawberry.field
        @upper_case
        def greeting(self) -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { greeting }")

    assert not result.errors
    assert result.data == {"greeting": "HI"}


def test_decorator_with_arguments():
    def suffix(value):
        def decorator(resolver):
            @wraps(resolver)
            def wrapper(*args, **kwargs):
                result = resolver(*args, **kwargs)

                return f"{result}{value}"

            return wrapper

        return decorator

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
    def upper_case(resolver):
        @functools.wraps(resolver)
        def wrap(*args, **kwargs):
            result = resolver(*args, **kwargs)
            return result.upper()

        return wrap

    def suffix(value):
        def decorator(resolver):
            @wraps(resolver)
            def wrapper(*args, **kwargs):
                result = resolver(*args, **kwargs)

                return f"{result}{value}"

            return wrapper

        return decorator

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
    def upper_case(resolver):
        @functools.wraps(resolver)
        def wrap(*args, **kwargs):
            result = resolver(*args, **kwargs)
            return result.upper()

        return wrap

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
        def decorator(resolver):
            @functools.wraps(resolver)
            def wrapped(*args, **kwargs):
                kwargs[argument_name] = kwargs[argument_name].title()
                return resolver(*args, **kwargs)

            return wrapped

        return decorator

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


def test_decorator_with_info():
    def upper_case(resolver):
        @wraps(resolver)
        def wrapped(*args, **kwargs):
            return resolver(*args, **kwargs).upper()

        return wrapped

    @strawberry.type
    class Query:
        @strawberry.field
        @upper_case
        def greeting(self, info: Info) -> str:
            return str(info.context)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { greeting }")

    assert not result.errors
    assert result.data == {"greeting": "NONE"}
