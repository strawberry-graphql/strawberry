from __future__ import annotations

import strawberry
from strawberry.schema_directives import OneOf


@strawberry.input(directives=[OneOf()])
class TestInputObject:
    a: str | None = strawberry.UNSET
    b: int | None = strawberry.UNSET


@strawberry.type
class TestObject:
    a: str | None
    b: int | None


@strawberry.type
class Query:
    @strawberry.field
    def test(self, input: TestInputObject) -> TestObject:
        return input  # type: ignore


schema = strawberry.Schema(query=Query)


def test_accepts_a_good_default_value():
    query = """
        query ($input: TestInputObject! = {a: "abc"}) {
          test(input: $input) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(query)

    assert result.data == {"test": {"a": "abc", "b": None}}


def test_error_with_bad_default_value():
    query = """
        query ($input: TestInputObject! = {a: "abc", b: 123}) {
          test(input: $input) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(query)

    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == (
        "OneOf Input Object 'TestInputObject' must specify exactly one key."
    )


def test_errors_when_passing_explicit_none_in_default():
    query = """
        query ($input: TestInputObject! = {a: "abc", b: null}) {
          test(input: $input) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(query)

    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == (
        "OneOf Input Object 'TestInputObject' must specify exactly one key."
    )


def test_works_with_good_value():
    query = """
        query ($input: TestInputObject!) {
          test(input: $input) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(query, variable_values={"input": {"a": "abc"}})

    assert result.data == {"test": {"a": "abc", "b": None}}


def test_error_with_bad_value():
    query = """
        query ($input: TestInputObject!) {
          test(input: $input) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(
        query, variable_values={"input": {"a": "abc", "b": 123}}
    )

    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == (
        "OneOf Input Object 'TestInputObject' must specify exactly one key."
    )


def test_errors_when_passing_explicit_none():
    query = """
        query ($input: TestInputObject! = {a: "abc", b: null}) {
          test(input: $input) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(query)

    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == (
        "OneOf Input Object 'TestInputObject' must specify exactly one key."
    )
