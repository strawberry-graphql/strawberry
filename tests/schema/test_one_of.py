from typing import Any

import pytest

import strawberry
from strawberry.schema_directives import OneOf


@strawberry.input(one_of=True)
class MaybeOneOfInput:
    a: strawberry.Maybe[str | None]
    b: strawberry.Maybe[int | None]


@strawberry.input(one_of=True)
class NullableOneOfInput:
    a: str | None
    b: int | None


@strawberry.type
class ExampleResult:
    a: str | None
    b: int | None


@strawberry.type
class Query:
    @strawberry.field
    def maybe_test(self, input: MaybeOneOfInput) -> ExampleResult:
        if input.a:
            return ExampleResult(a=input.a.value, b=None)
        if input.b:
            return ExampleResult(a=None, b=input.b.value)
        return ExampleResult(a=None, b=None)

    @strawberry.field
    def nullable_test(self, input: NullableOneOfInput) -> ExampleResult:
        return ExampleResult(a=input.a, b=input.b)


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
@pytest.mark.parametrize(
    ("query_template", "expected_input_name"),
    [
        (
            "query ($input: MaybeOneOfInput! = {default_value}) {{ maybeTest(input: $input) {{ a b }} }}",
            "MaybeOneOfInput",
        ),
        (
            "query ($input: NullableOneOfInput! = {default_value}) {{ nullableTest(input: $input) {{ a b }} }}",
            "NullableOneOfInput",
        ),
    ],
)
def test_must_specify_at_least_one_key_default(
    query_template: str,
    default_value: str,
    variables: dict[str, Any],
    expected_input_name: str,
):
    query = query_template.format(default_value=default_value)

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == f"OneOf Input Object '{expected_input_name}' must specify exactly one key."
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
@pytest.mark.parametrize(
    ("query_template", "input_name"),
    [
        (
            "query {variable_definitions} {{ maybeTest(input: {value}) {{ a b }} }}",
            "MaybeOneOfInput",
        ),
        (
            "query {variable_definitions} {{ nullableTest(input: {value}) {{ a b }} }}",
            "NullableOneOfInput",
        ),
    ],
)
def test_must_specify_at_least_one_key_literal(
    query_template: str, value: str, variables: dict[str, Any], input_name: str
):
    variables_definitions = []

    if "$a" in value:
        variables_definitions.append("$a: String")

    if "$b" in value:
        variables_definitions.append("$b: Int")

    if "$input" in value:
        variables_definitions.append(f"$input: {input_name}!")

    variables_definition_str = (
        f"({', '.join(variables_definitions)})" if variables_definitions else ""
    )

    query = query_template.format(
        variable_definitions=variables_definition_str, value=value
    )

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == f"OneOf Input Object '{input_name}' must specify exactly one key."
    )


@pytest.mark.parametrize(
    "query",
    [
        "query ($input: MaybeOneOfInput!) { maybeTest(input: $input) { b } } ",
        "query ($input: NullableOneOfInput!) { nullableTest(input: $input) { b } } ",
    ],
)
def test_value_must_be_non_null_input(query: str):
    result = schema.execute_sync(query, variable_values={"input": {"a": None}})

    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == "Value for member field 'a' must be non-null"


@pytest.mark.parametrize(
    ("query", "expected_input_name"),
    [
        ("query { maybeTest(input: { a: null }) { a b } } ", "MaybeOneOfInput"),
        ("query { nullableTest(input: { a: null }) { a b } } ", "NullableOneOfInput"),
    ],
)
def test_value_must_be_non_null_literal(query: str, expected_input_name: str):
    result = schema.execute_sync(query, variable_values={"input": {"a": None}})

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message == f"Field '{expected_input_name}.a' must be non-null."
    )


@pytest.mark.parametrize(
    ("query", "expected_input_name"),
    [
        ("query ($b: Int) { maybeTest(input: { b: $b }) { a b } } ", "MaybeOneOfInput"),
        (
            "query ($b: Int) { nullableTest(input: { b: $b }) { a b } } ",
            "NullableOneOfInput",
        ),
    ],
)
def test_value_must_be_non_null_variable(query: str, expected_input_name: str):
    result = schema.execute_sync(query, variable_values={})

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == f"Variable 'b' must be non-nullable to be used for OneOf Input Object '{expected_input_name}'."
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
@pytest.mark.parametrize(
    ("field_name", "input_name"),
    [
        ("maybeTest", "MaybeOneOfInput"),
        ("nullableTest", "NullableOneOfInput"),
    ],
)
def test_works(
    field_name: str,
    input_name: str,
    value: str,
    variables: dict[str, Any],
    expected: dict[str, Any],
):
    variables_definitions = []

    if "$b" in value:
        variables_definitions.append("$b: Int!")

    if "$input" in value:
        variables_definitions.append(f"$input: {input_name}!")

    variables_definition_str = (
        f"({', '.join(variables_definitions)})" if variables_definitions else ""
    )

    output_field = next(iter(expected.keys()))

    query = f"""
        query {variables_definition_str} {{
          {field_name}(input: {value}) {{
            {output_field}
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert not result.errors
    assert result.data == {field_name: expected}


def test_works_with_camelcasing():
    global ExampleWithLongerNames, Result

    @strawberry.input(directives=[OneOf()])
    class ExampleWithLongerNames:
        a_field: strawberry.Maybe[str | None]
        b_field: strawberry.Maybe[int | None]

    @strawberry.type
    class Result:
        a_field: str | None
        b_field: int | None

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
          maybe: __type(name: "MaybeOneOfInput") {
            name
            isOneOf
          }
          nullable: __type(name: "NullableOneOfInput") {
            name
            isOneOf
          }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {
        "maybe": {"name": "MaybeOneOfInput", "isOneOf": True},
        "nullable": {"name": "NullableOneOfInput", "isOneOf": True},
    }


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
