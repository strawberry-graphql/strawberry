import textwrap
from enum import Enum
from typing import Annotated

import pytest
from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLScalarType,
    build_schema,
    get_named_type,
    specified_directives,
)

import strawberry
import strawberry.schema.schema as schema_module
from strawberry.exceptions import (
    DuplicatedTypeName,
    DuplicateSchemaDirectiveError,
    InvalidSchemaDirectiveLocationError,
    UnresolvedFieldTypeError,
)
from strawberry.schema.schema_converter import GraphQLCoreConverter
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

    expected = """
    directive @marker(name: String!) repeatable on SCHEMA | OBJECT | FIELD_DEFINITION

    schema @marker(name: "schema") {
      query: Query
    }

    type Query @marker(name: "object-1") @marker(name: "object-2") {
      name: String! @marker(name: "field")
    }
    """

    sdl = schema.as_str()
    assert sdl == textwrap.dedent(expected).strip()
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

    expected = """
    directive @marker on OBJECT

    type Query @marker {
      name: String!
    }
    """

    sdl = schema.as_str()
    assert sdl == textwrap.dedent(expected).strip()
    build_schema(sdl)


def test_plain_subclass_reuses_inherited_directive_definition():
    @strawberry.schema_directive(locations=[Location.OBJECT, Location.FIELD_DEFINITION])
    class Marker: ...

    class FieldMarker(Marker): ...

    @strawberry.type(directives=[Marker()])
    class Query:
        name: str = strawberry.field(default="Patrick", directives=[FieldMarker()])

    schema = strawberry.Schema(query=Query)

    assert (
        sum(directive.name == "marker" for directive in schema._schema.directives) == 1
    )

    expected = """
    directive @marker on OBJECT | FIELD_DEFINITION

    type Query @marker {
      name: String! @marker
    }
    """

    sdl = schema.as_str()
    assert sdl == textwrap.dedent(expected).strip()
    build_schema(sdl)


def test_registers_nested_directive_argument_input_types():
    @strawberry.schema_directive(locations=[Location.INPUT_OBJECT])
    class OnNestedInput: ...

    @strawberry.schema_directive(locations=[Location.INPUT_FIELD_DEFINITION])
    class OnNestedInputField: ...

    @strawberry.enum
    class Mode(Enum):
        PRIVATE = "private"

    Secret = strawberry.scalar(str, name="Secret")

    @strawberry.input(directives=[OnNestedInput()])
    class Rule:
        value: str = strawberry.field(directives=[OnNestedInputField()])

    @strawberry.input
    class Policy:
        rule: Rule
        mode: Mode
        secret: Secret

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Protected:
        policy: Policy | None = strawberry.UNSET

    @strawberry.type
    class Query:
        name: str = strawberry.field(
            default="Patrick",
            directives=[Protected()],
        )

    schema = strawberry.Schema(query=Query)

    policy_type = schema._schema.get_type("Policy")
    rule_type = schema._schema.get_type("Rule")
    assert isinstance(policy_type, GraphQLInputObjectType)
    assert isinstance(rule_type, GraphQLInputObjectType)
    assert isinstance(schema._schema.get_type("Mode"), GraphQLEnumType)
    assert isinstance(schema._schema.get_type("Secret"), GraphQLScalarType)
    assert get_named_type(policy_type.fields["rule"].type) is rule_type
    assert schema._schema.get_directive("onNestedInput") is not None
    assert schema._schema.get_directive("onNestedInputField") is not None

    expected = """
    directive @onNestedInput on INPUT_OBJECT

    directive @onNestedInputField on INPUT_FIELD_DEFINITION

    directive @protected(policy: Policy) on FIELD_DEFINITION

    enum Mode {
      PRIVATE
    }

    input Policy {
      rule: Rule!
      mode: Mode!
      secret: Secret!
    }

    type Query {
      name: String! @protected
    }

    input Rule @onNestedInput {
      value: String! @onNestedInputField
    }

    scalar Secret
    """

    sdl = schema.as_str()
    assert sdl == textwrap.dedent(expected).strip()
    build_schema(sdl)


def test_print_definition_false_remains_available_to_introspection():
    @strawberry.input
    class HiddenConfig:
        reason: str

    @strawberry.schema_directive(
        locations=[Location.FIELD_DEFINITION], print_definition=False
    )
    class Hidden:
        config: HiddenConfig | None = strawberry.UNSET

    @strawberry.type
    class Query:
        name: str = strawberry.field(
            default="Patrick",
            directives=[Hidden()],
        )

    schema = strawberry.Schema(query=Query)

    assert schema._schema.get_directive("hidden") is not None
    assert schema._schema.get_type("HiddenConfig") is not None

    expected = """
    input HiddenConfig {
      reason: String!
    }

    type Query {
      name: String! @hidden
    }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_hidden_argument_types_are_printed_with_visible_directive_definitions():
    HiddenValue = strawberry.scalar(str, name="HiddenValue", print_definition=False)

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Marker:
        value: HiddenValue

    @strawberry.type
    class Query:
        name: str = strawberry.field(
            default="Patrick",
            directives=[Marker(value="example")],
        )

    schema = strawberry.Schema(query=Query)

    expected = """
    directive @marker(value: HiddenValue!) on FIELD_DEFINITION

    scalar HiddenValue

    type Query {
      name: String! @marker(value: "example")
    }
    """

    sdl = schema.as_str()
    assert sdl == textwrap.dedent(expected).strip()
    build_schema(sdl)


def test_registers_directives_from_all_type_system_attachment_points():
    def directive(name: str, location: Location) -> type:
        @strawberry.schema_directive(name=name, locations=[location])
        class Directive: ...

        return Directive

    SchemaDirective = directive("onSchema", Location.SCHEMA)
    ScalarDirective = directive("onScalar", Location.SCALAR)
    ObjectDirective = directive("onObject", Location.OBJECT)
    FieldDirective = directive("onField", Location.FIELD_DEFINITION)
    ArgumentDirective = directive("onArgument", Location.ARGUMENT_DEFINITION)
    InterfaceDirective = directive("onInterface", Location.INTERFACE)
    UnionDirective = directive("onUnion", Location.UNION)
    EnumDirective = directive("onEnum", Location.ENUM)
    EnumValueDirective = directive("onEnumValue", Location.ENUM_VALUE)
    InputDirective = directive("onInput", Location.INPUT_OBJECT)
    InputFieldDirective = directive("onInputField", Location.INPUT_FIELD_DEFINITION)

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

    @strawberry.type(directives=[ObjectDirective()])
    class Query:
        node: Node = strawberry.field(directives=[FieldDirective()])
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

    schema = strawberry.Schema(
        query=Query,
        types=[Item],
        schema_directives=[SchemaDirective()],
    )
    directive_names = {item.name for item in schema._schema.directives}

    assert {
        "onSchema",
        "onScalar",
        "onObject",
        "onField",
        "onArgument",
        "onInterface",
        "onUnion",
        "onEnum",
        "onEnumValue",
        "onInput",
        "onInputField",
    } <= directive_names

    sdl = schema.as_str()
    assert "schema @onSchema {" in sdl
    assert "scalar CustomScalar @onScalar" in sdl
    assert "type Query @onObject {" in sdl
    assert "node: Node! @onField" in sdl
    assert "term: String! @onArgument" in sdl
    assert "interface Node @onInterface" in sdl
    assert "union Result @onUnion" in sdl
    assert "enum Choice @onEnum" in sdl
    assert "FIRST @onEnumValue" in sdl
    assert "input Filter @onInput" in sdl
    assert "term: String! @onInputField" in sdl
    build_schema(sdl)


def test_rejects_object_directive_on_interface():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class Marker: ...

    @strawberry.interface(directives=[Marker()])
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Query:
        node: Node

    with pytest.raises(
        InvalidSchemaDirectiveLocationError,
        match=(
            r"Schema directive '@marker' cannot be applied to INTERFACE schema "
            r"element 'Node'\. Allowed locations: OBJECT\."
        ),
    ):
        strawberry.Schema(query=Query)


def test_rejects_field_directive_on_schema():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Marker: ...

    @strawberry.type
    class Query:
        value: str

    with pytest.raises(
        InvalidSchemaDirectiveLocationError,
        match=(
            r"Schema directive '@marker' cannot be applied to SCHEMA schema "
            r"element 'schema'\. Allowed locations: FIELD_DEFINITION\."
        ),
    ):
        strawberry.Schema(query=Query, schema_directives=[Marker()])


def test_rejects_output_field_directive_on_input_field():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Marker: ...

    @strawberry.input
    class Filter:
        value: str = strawberry.field(directives=[Marker()])

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: Filter) -> str:
            return filter.value

    with pytest.raises(
        InvalidSchemaDirectiveLocationError,
        match=(
            r"Schema directive '@marker' cannot be applied to "
            r"INPUT_FIELD_DEFINITION schema element 'Filter.value'\. Allowed "
            r"locations: FIELD_DEFINITION\."
        ),
    ):
        strawberry.Schema(query=Query)


def test_rejects_input_field_directive_on_output_field():
    @strawberry.schema_directive(locations=[Location.INPUT_FIELD_DEFINITION])
    class Marker: ...

    @strawberry.type
    class Query:
        value: str = strawberry.field(directives=[Marker()])

    with pytest.raises(
        InvalidSchemaDirectiveLocationError,
        match=(
            r"Schema directive '@marker' cannot be applied to FIELD_DEFINITION "
            r"schema element 'Query.value'\. Allowed locations: "
            r"INPUT_FIELD_DEFINITION\."
        ),
    ):
        strawberry.Schema(query=Query)


def test_rejects_scalar_directive_on_union():
    @strawberry.schema_directive(locations=[Location.SCALAR])
    class Marker: ...

    @strawberry.type
    class Item:
        name: str

    @strawberry.type
    class Other:
        value: str

    Result = Annotated[
        Item | Other,
        strawberry.union("Result", directives=[Marker()]),
    ]

    @strawberry.type
    class Query:
        result: Result

    with pytest.raises(
        InvalidSchemaDirectiveLocationError,
        match=(
            r"Schema directive '@marker' cannot be applied to UNION schema "
            r"element 'Result'\. Allowed locations: SCALAR\."
        ),
    ):
        strawberry.Schema(query=Query)


def test_rejects_duplicate_non_repeatable_directive():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Marker:
        value: str

    @strawberry.type
    class Query:
        value: str = strawberry.field(
            directives=[Marker(value="first"), Marker(value="second")]
        )

    with pytest.raises(
        DuplicateSchemaDirectiveError,
        match=(
            r"Schema directive '@marker' is not repeatable and cannot be applied "
            r"more than once to FIELD_DEFINITION schema element 'Query.value'\."
        ),
    ):
        strawberry.Schema(query=Query)


def test_non_repeatable_directive_can_be_reused_on_separate_elements():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Marker: ...

    @strawberry.type
    class Query:
        first: str = strawberry.field(directives=[Marker()])
        second: str = strawberry.field(directives=[Marker()])

    schema = strawberry.Schema(query=Query)
    sdl = schema.as_str()

    assert "first: String! @marker" in sdl
    assert "second: String! @marker" in sdl
    build_schema(sdl)


def test_directives_passed_as_one_shot_iterables_are_kept():
    @strawberry.schema_directive(
        locations=[
            Location.ARGUMENT_DEFINITION,
            Location.ENUM,
            Location.ENUM_VALUE,
            Location.SCALAR,
            Location.UNION,
        ]
    )
    class Marker: ...

    def markers():
        yield Marker()

    @strawberry.enum(directives=markers())
    class Choice(Enum):
        FIRST = strawberry.enum_value("first", directives=markers())

    CustomScalar = strawberry.scalar(str, name="CustomScalar", directives=markers())

    @strawberry.type
    class Item:
        name: str

    @strawberry.type
    class Other:
        value: str

    Result = Annotated[Item | Other, strawberry.union("Result", directives=markers())]

    @strawberry.type
    class Query:
        result: Result
        custom_scalar: CustomScalar

        @strawberry.field
        def choice(
            self,
            choice: Annotated[Choice, strawberry.argument(directives=markers())],
        ) -> Choice:
            return choice

    schema = strawberry.Schema(query=Query)

    expected = """
    directive @marker on ARGUMENT_DEFINITION | ENUM | ENUM_VALUE | SCALAR | UNION

    enum Choice @marker {
      FIRST @marker
    }

    scalar CustomScalar @marker

    type Item {
      name: String!
    }

    type Other {
      value: String!
    }

    type Query {
      result: Result!
      customScalar: CustomScalar!
      choice(choice: Choice! @marker): Choice!
    }

    union Result @marker = Item | Other
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
    assert schema._schema.get_directive("marker") is not None


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


def test_compatible_custom_one_of_uses_specified_directive():
    @strawberry.schema_directive(name="oneOf", locations=[Location.INPUT_OBJECT])
    class LegacyOneOf: ...

    @strawberry.input(directives=[LegacyOneOf()])
    class Choice:
        value: str | None

    @strawberry.type
    class Query:
        @strawberry.field
        def choose(self, choice: Choice) -> str:
            return choice.value or ""

    schema = strawberry.Schema(query=Query)

    expected = """
    directive @oneOf on INPUT_OBJECT

    input Choice @oneOf {
      value: String
    }

    type Query {
      choose(choice: Choice!): String!
    }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
    assert schema._schema.get_directive("oneOf") is not None


@pytest.mark.skipif(
    not any(directive.name == "oneOf" for directive in specified_directives),
    reason="graphql-core does not define the specified @oneOf directive",
)
def test_rejects_custom_one_of_with_a_different_description():
    @strawberry.schema_directive(
        name="oneOf",
        description="A custom oneOf definition.",
        locations=[Location.INPUT_OBJECT],
    )
    class CustomOneOf: ...

    @strawberry.input(directives=[CustomOneOf()])
    class Choice:
        value: str | None

    @strawberry.type
    class Query:
        @strawberry.field
        def choose(self, choice: Choice) -> str:
            return choice.value or ""

    with pytest.raises(
        ValueError,
        match=(
            r"Schema directive '@oneOf' is defined by both the built-in GraphQL "
            r"directive and schema directive .*CustomOneOf"
        ),
    ):
        strawberry.Schema(query=Query)


def test_rejects_directive_argument_type_name_conflicts():
    @strawberry.input(name="Conflict")
    class DirectiveInput:
        value: str

    @strawberry.type(name="Conflict")
    class RegularType:
        value: str

    @strawberry.schema_directive(locations=[Location.OBJECT])
    class Marker:
        config: DirectiveInput

    @strawberry.type(directives=[Marker(config=DirectiveInput(value="directive"))])
    class Query:
        value: RegularType

    with pytest.raises(
        DuplicatedTypeName,
        match="Type Conflict is defined multiple times in the schema",
    ):
        strawberry.Schema(query=Query)


def test_constructs_graphql_schema_and_directive_definitions_once(monkeypatch):
    @strawberry.schema_directive(locations=[Location.INPUT_OBJECT])
    class OnConfig: ...

    @strawberry.input(directives=[OnConfig()])
    class Config:
        value: str

    @strawberry.schema_directive(locations=[Location.OBJECT])
    class Marker:
        config: Config

    @strawberry.type(directives=[Marker(config=Config(value="example"))])
    class Query:
        value: str

    graphql_schema_calls = 0
    converted_directives: list[type] = []
    graphql_schema = schema_module.GraphQLSchema
    from_schema_directive = GraphQLCoreConverter.from_schema_directive

    def counting_graphql_schema(*args: object, **kwargs: object):
        nonlocal graphql_schema_calls
        graphql_schema_calls += 1
        return graphql_schema(*args, **kwargs)

    def counting_from_schema_directive(self, directive_type):
        converted_directives.append(directive_type)
        return from_schema_directive(self, directive_type)

    monkeypatch.setattr(schema_module, "GraphQLSchema", counting_graphql_schema)
    monkeypatch.setattr(
        GraphQLCoreConverter,
        "from_schema_directive",
        counting_from_schema_directive,
    )

    schema = strawberry.Schema(query=Query)
    schema.as_str()

    assert graphql_schema_calls == 1
    assert converted_directives == [Marker, OnConfig]


def test_reports_unresolved_directive_argument_types():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class Marker:
        config: "MissingConfig"  # noqa: F821

    @strawberry.type(directives=[Marker(config=None)])  # type: ignore[arg-type]
    class Query:
        name: str

    with pytest.raises(
        UnresolvedFieldTypeError,
        match=(
            r"Could not resolve the type of 'config'\. Check that the class is "
            r"accessible from the global module scope\."
        ),
    ):
        strawberry.Schema(query=Query)
