from typing import Any, Union

import pytest

import strawberry
from strawberry.schema_directives import OneOf


@strawberry.input(one_of=True)
class ExampleInputTagged:
    a: strawberry.Maybe[str]
    b: strawberry.Maybe[int]


@strawberry.type
class ExampleResult:
    a: Union[str, None]
    b: Union[int, None]


@strawberry.type
class Query:
    @strawberry.field
    def test(self, input: ExampleInputTagged) -> ExampleResult:
        if input.a:
            return ExampleResult(a=input.a.value, b=None)
        if input.b:
            return ExampleResult(a=None, b=input.b.value)
        return ExampleResult(a=None, b=None)


schema = strawberry.Schema(query=Query)


@pytest.mark.parametrize(
    ("default_value", "variables"),
    [
        ("{a: null, b: null}", {}),
        ('{ a: "abc", b: 123 }', {}),
        ("{a: null, b: 123}", {}),
        ("{}", {}),
    ],
)
def test_must_specify_at_least_one_key_default(
    default_value: str, variables: dict[str, Any]
):
    query = f"""
        query ($input: ExampleInputTagged! = {default_value}) {{
          test(input: $input) {{
            a
            b
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "OneOf Input Object 'ExampleInputTagged' must specify exactly one key."
    )


@pytest.mark.parametrize(
    ("value", "variables"),
    [
        ("{a: null, b: null}", {}),
        ('{ a: "abc", b: 123 }', {}),
        ("{a: null, b: 123}", {}),
        ("{}", {}),
        ("{ a: $a, b: 123 }", {"a": "abc"}),
        ("{ a: $a, b: 123 }", {}),
        ("{ a: $a, b: $b }", {"a": "abc"}),
        ("$input", {"input": {"a": "abc", "b": 123}}),
        ("$input", {"input": {"a": "abc", "b": None}}),
        ("$input", {"input": {}}),
        ('{ a: "abc", b: null }', {}),
    ],
)
def test_must_specify_at_least_one_key_literal(value: str, variables: dict[str, Any]):
    variables_definitions = []

    if "$a" in value:
        variables_definitions.append("$a: String")

    if "$b" in value:
        variables_definitions.append("$b: Int")

    if "$input" in value:
        variables_definitions.append("$input: ExampleInputTagged!")

    variables_definition_str = (
        f"({', '.join(variables_definitions)})" if variables_definitions else ""
    )

    query = f"""
        query {variables_definition_str} {{
          test(input: {value}) {{
            a
            b
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "OneOf Input Object 'ExampleInputTagged' must specify exactly one key."
    )


def test_value_must_be_non_null_input():
    query = """
        query ($input: ExampleInputTagged!) {
          test(input: $input) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(query, variable_values={"input": {"a": None}})

    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == "Value for member field 'a' must be non-null"


def test_value_must_be_non_null_literal():
    query = """
        query {
          test(input: { a: null }) {
            a
            b
          }
        }
    """

    result = schema.execute_sync(query, variable_values={"input": {"a": None}})

    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == "Field 'ExampleInputTagged.a' must be non-null."


def test_value_must_be_non_null_variable():
    query = """
        query ($b: Int) {
            test(input: { b: $b }) {
                b
            }
        }
    """

    result = schema.execute_sync(query, variable_values={})

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "Variable 'b' must be non-nullable to be used for OneOf Input Object 'ExampleInputTagged'."
    )


@pytest.mark.parametrize(
    ("value", "variables", "expected"),
    [
        ("{ b: $b }", {"b": 123}, {"b": 123}),
        ("$input", {"input": {"b": 123}}, {"b": 123}),
        ('{ a: "abc" }', {}, {"a": "abc"}),
        ("$input", {"input": {"a": "abc"}}, {"a": "abc"}),
    ],
)
def test_works(value: str, variables: dict[str, Any], expected: dict[str, Any]):
    variables_definitions = []

    if "$b" in value:
        variables_definitions.append("$b: Int!")

    if "$input" in value:
        variables_definitions.append("$input: ExampleInputTagged!")

    variables_definition_str = (
        f"({', '.join(variables_definitions)})" if variables_definitions else ""
    )

    field = next(iter(expected.keys()))

    query = f"""
        query {variables_definition_str} {{
          test(input: {value}) {{
            {field}
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert not result.errors
    assert result.data["test"] == expected


def test_works_with_camelcasing():
    global ExampleWithLongerNames, Result

    @strawberry.input(directives=[OneOf()])
    class ExampleWithLongerNames:
        a_field: strawberry.Maybe[str]
        b_field: strawberry.Maybe[int]

    @strawberry.type
    class Result:
        a_field: Union[str, None]
        b_field: Union[int, None]

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, input: ExampleWithLongerNames) -> Result:
            return Result(  # noqa: F821
                a_field=input.a_field.value if input.a_field else None,
                b_field=input.b_field.value if input.b_field else None,
            )

    schema = strawberry.Schema(query=Query)

    query = """
        query ($input: ExampleWithLongerNames!) {
          test(input: $input) {
            aField
            bField
          }
        }
    """

    result = schema.execute_sync(query, variable_values={"input": {"aField": "abc"}})

    assert not result.errors
    assert result.data["test"] == {"aField": "abc", "bField": None}

    del ExampleWithLongerNames, Result


def test_introspection():
    query = """
        query {
          __type(name: "ExampleInputTagged") {
            name
            isOneOf
          }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {"__type": {"name": "ExampleInputTagged", "isOneOf": True}}


def test_introspection_builtin():
    query = """
        query {
          __type(name: "String") {
            name
            isOneOf
          }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {"__type": {"name": "String", "isOneOf": False}}
