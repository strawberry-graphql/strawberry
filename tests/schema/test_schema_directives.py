from enum import Enum
from typing import Annotated

import pytest
from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLScalarType,
    build_schema,
    get_named_type,
)

import strawberry
from strawberry.schema_directive import Location


def test_registers_reused_directives_and_preserves_application_order():
    @strawberry.schema_directive(
        locations=[Location.SCHEMA, Location.OBJECT, Location.FIELD_DEFINITION],
        repeatable=True,
    )
    class Marker:
        name: str

    @strawberry.type(directives=[Marker(name="object-1"), Marker(name="object-2")])
    class Query:
        name: str = strawberry.field(
            default="Patrick", directives=[Marker(name="field")]
        )

    schema = strawberry.Schema(query=Query, schema_directives=[Marker(name="schema")])

    directives = [
        directive
        for directive in schema._schema.directives
        if directive.name == "marker"
    ]
    assert len(directives) == 1

    sdl = schema.as_str()
    assert sdl.count("directive @marker") == 1
    assert 'schema @marker(name: "schema")' in sdl
    assert 'type Query @marker(name: "object-1") @marker(name: "object-2")' in sdl
    assert 'name: String! @marker(name: "field")' in sdl
    build_schema(sdl)


def test_introspection_exposes_schema_directive_metadata():
    @strawberry.schema_directive(
        name="accessPolicy",
        description="Controls access to a schema element.",
        locations=[Location.OBJECT, Location.FIELD_DEFINITION],
        repeatable=True,
    )
    class AccessPolicy:
        role: str
        level: int = 1

    @strawberry.type(directives=[AccessPolicy(role="admin")])
    class Query:
        name: str

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
        {
          __schema {
            directives {
              name
              description
              isRepeatable
              locations
              args {
                name
                defaultValue
                type {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
        """
    )

    assert result.errors is None
    directive = next(
        directive
        for directive in result.data["__schema"]["directives"]
        if directive["name"] == "accessPolicy"
    )
    assert directive == {
        "name": "accessPolicy",
        "description": "Controls access to a schema element.",
        "isRepeatable": True,
        "locations": ["OBJECT", "FIELD_DEFINITION"],
        "args": [
            {
                "name": "role",
                "defaultValue": None,
                "type": {
                    "kind": "NON_NULL",
                    "name": None,
                    "ofType": {"kind": "SCALAR", "name": "String"},
                },
            },
            {
                "name": "level",
                "defaultValue": "1",
                "type": {
                    "kind": "NON_NULL",
                    "name": None,
                    "ofType": {"kind": "SCALAR", "name": "Int"},
                },
            },
        ],
    }


def test_explicit_directive_type_is_reconciled_with_attached_uses():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class Marker: ...

    @strawberry.type(directives=[Marker()])
    class Query:
        name: str

    schema = strawberry.Schema(query=Query, types=[Marker, Marker])

    assert (
        sum(directive.name == "marker" for directive in schema._schema.directives) == 1
    )
    sdl = schema.as_str()
    assert sdl.count("directive @marker") == 1
    build_schema(sdl)


def test_registers_nested_directive_argument_input_types():
    @strawberry.enum
    class Mode(Enum):
        PRIVATE = "private"

    Secret = strawberry.scalar(str, name="Secret")

    @strawberry.input
    class Rule:
        value: str

    @strawberry.input
    class Policy:
        rule: Rule
        mode: Mode
        secret: Secret

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Protected:
        policy: Policy

    @strawberry.type
    class Query:
        name: str = strawberry.field(
            default="Patrick",
            directives=[
                Protected(
                    policy=Policy(
                        rule=Rule(value="private"),
                        mode=Mode.PRIVATE,
                        secret="token",
                    )
                )
            ],
        )

    schema = strawberry.Schema(query=Query)

    policy_type = schema._schema.get_type("Policy")
    rule_type = schema._schema.get_type("Rule")
    assert isinstance(policy_type, GraphQLInputObjectType)
    assert isinstance(rule_type, GraphQLInputObjectType)
    assert isinstance(schema._schema.get_type("Mode"), GraphQLEnumType)
    assert isinstance(schema._schema.get_type("Secret"), GraphQLScalarType)
    assert get_named_type(policy_type.fields["rule"].type) is rule_type

    sdl = schema.as_str()
    assert sdl.count("input Policy") == 1
    assert sdl.count("input Rule") == 1
    assert sdl.count("enum Mode") == 1
    assert sdl.count("scalar Secret") == 1
    build_schema(sdl)


def test_print_definition_false_remains_available_to_introspection():
    @strawberry.input
    class HiddenConfig:
        reason: str

    @strawberry.schema_directive(
        locations=[Location.FIELD_DEFINITION], print_definition=False
    )
    class Hidden:
        config: HiddenConfig

    @strawberry.type
    class Query:
        name: str = strawberry.field(
            default="Patrick",
            directives=[Hidden(config=HiddenConfig(reason="private"))],
        )

    schema = strawberry.Schema(query=Query)

    assert schema._schema.get_directive("hidden") is not None
    assert schema._schema.get_type("HiddenConfig") is not None

    sdl = schema.as_str()
    assert "directive @hidden" not in sdl
    assert "input HiddenConfig" not in sdl
    assert "@hidden(config:" in sdl
    assert 'reason: "private"' in sdl


def test_registers_directives_from_all_type_system_attachment_points():
    def directive(name: str, location: Location) -> type:
        @strawberry.schema_directive(name=name, locations=[location])
        class Directive: ...

        return Directive

    InterfaceDirective = directive("onInterface", Location.INTERFACE)
    UnionDirective = directive("onUnion", Location.UNION)
    EnumDirective = directive("onEnum", Location.ENUM)
    EnumValueDirective = directive("onEnumValue", Location.ENUM_VALUE)
    ScalarDirective = directive("onScalar", Location.SCALAR)
    InputDirective = directive("onInput", Location.INPUT_OBJECT)
    InputFieldDirective = directive("onInputField", Location.INPUT_FIELD_DEFINITION)
    ArgumentDirective = directive("onArgument", Location.ARGUMENT_DEFINITION)

    @strawberry.interface(directives=[InterfaceDirective()])
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Item(Node):
        name: str

    @strawberry.type
    class Other:
        value: str

    Result = Annotated[
        Item | Other,
        strawberry.union("Result", directives=[UnionDirective()]),
    ]

    @strawberry.enum(directives=[EnumDirective()])
    class Choice(Enum):
        FIRST = strawberry.enum_value("first", directives=[EnumValueDirective()])

    CustomScalar = strawberry.scalar(
        str, name="CustomScalar", directives=[ScalarDirective()]
    )

    @strawberry.input(directives=[InputDirective()])
    class Filter:
        term: str = strawberry.field(directives=[InputFieldDirective()])

    @strawberry.type
    class Query:
        node: Node
        result: Result
        choice: Choice
        custom_scalar: CustomScalar

        @strawberry.field
        def search(
            self,
            filter: Filter,
            term: Annotated[str, strawberry.argument(directives=[ArgumentDirective()])],
        ) -> str:
            return filter.term + term

    schema = strawberry.Schema(query=Query, types=[Item])
    directive_names = {item.name for item in schema._schema.directives}

    assert {
        "onInterface",
        "onUnion",
        "onEnum",
        "onEnumValue",
        "onScalar",
        "onInput",
        "onInputField",
        "onArgument",
    } <= directive_names


def test_rejects_conflicting_schema_directive_names():
    @strawberry.schema_directive(name="conflict", locations=[Location.OBJECT])
    class First: ...

    @strawberry.schema_directive(name="conflict", locations=[Location.FIELD_DEFINITION])
    class Second: ...

    @strawberry.type(directives=[First()])
    class Query:
        name: str = strawberry.field(default="Patrick", directives=[Second()])

    with pytest.raises(
        ValueError,
        match=(
            r"Schema directive '@conflict' is defined by both .*First.* and .*Second"
        ),
    ):
        strawberry.Schema(query=Query)


def test_rejects_schema_directive_collisions_with_specified_directives():
    @strawberry.schema_directive(name="skip", locations=[Location.OBJECT])
    class CustomSkip: ...

    @strawberry.type(directives=[CustomSkip()])
    class Query:
        name: str

    with pytest.raises(
        ValueError,
        match=(
            r"Schema directive '@skip' is defined by both the built-in GraphQL "
            "directive and schema directive .*CustomSkip"
        ),
    ):
        strawberry.Schema(query=Query)
