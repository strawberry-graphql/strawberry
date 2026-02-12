from __future__ import annotations

import dataclasses
import keyword
from collections import defaultdict
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, TypeAlias
from typing_extensions import Protocol

import libcst as cst
from graphql import (
    DirectiveDefinitionNode,
    EnumTypeDefinitionNode,
    EnumValueDefinitionNode,
    FieldDefinitionNode,
    InputObjectTypeDefinitionNode,
    InputValueDefinitionNode,
    InterfaceTypeDefinitionNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
    OperationType,
    ScalarTypeDefinitionNode,
    SchemaDefinitionNode,
    SchemaExtensionNode,
    StringValueNode,
    TypeNode,
    UnionTypeDefinitionNode,
    parse,
)
from graphql.language.ast import (
    BooleanValueNode,
    ConstValueNode,
    EnumValueNode,
    FloatValueNode,
    IntValueNode,
    ListValueNode,
    NullValueNode,
)

from strawberry.utils.str_converters import capitalize_first, to_snake_case

if TYPE_CHECKING:
    from graphql.language.ast import ConstDirectiveNode


class HasDirectives(Protocol):
    directives: tuple[ConstDirectiveNode, ...]


_SCALAR_MAP = {
    "Int": cst.Name("int"),
    "Float": cst.Name("float"),
    "Boolean": cst.Name("bool"),
    "String": cst.Name("str"),
    "ID": cst.Attribute(
        value=cst.Name("strawberry"),
        attr=cst.Name("ID"),
    ),
    "JSON": cst.Attribute(
        value=cst.Name("strawberry"),
        attr=cst.Name("JSON"),
    ),
    "UUID": cst.Name("UUID"),
    "Decimal": cst.Name("Decimal"),
    "Date": cst.Name("date"),
    "Time": cst.Name("time"),
    "DateTime": cst.Name("datetime"),
}

_FEDERATION_DIRECTIVE_NAMES = frozenset({
    "key",
    "shareable",
    "inaccessible",
    "external",
    "authenticated",
    "override",
    "requires",
    "provides",
    "tag",
    "requiresScopes",
    "policy",
    "link",
    "specifiedBy",
})

_STRAWBERRY_LOCATION_NAMES = frozenset({
    "SCHEMA",
    "SCALAR",
    "OBJECT",
    "FIELD_DEFINITION",
    "ARGUMENT_DEFINITION",
    "INTERFACE",
    "UNION",
    "ENUM",
    "ENUM_VALUE",
    "INPUT_OBJECT",
    "INPUT_FIELD_DEFINITION",
})


@dataclasses.dataclass(frozen=True)
class Import:
    module: str | None
    imports: tuple[str]

    def module_path_to_cst(self, module_path: str) -> cst.Name | cst.Attribute:
        parts = module_path.split(".")

        module_name: cst.Name | cst.Attribute = cst.Name(parts[0])

        for part in parts[1:]:
            module_name = cst.Attribute(value=module_name, attr=cst.Name(part))

        return module_name

    def to_cst(self) -> cst.Import | cst.ImportFrom:
        if self.module is None:
            return cst.Import(
                names=[cst.ImportAlias(name=cst.Name(name)) for name in self.imports]
            )

        return cst.ImportFrom(
            module=self.module_path_to_cst(self.module),
            names=[cst.ImportAlias(name=cst.Name(name)) for name in self.imports],
        )


def _is_federation_link_directive(directive: ConstDirectiveNode) -> bool:
    if directive.name.value != "link":
        return False

    return next(
        (
            argument.value.value
            for argument in directive.arguments
            if argument.name.value == "url"
            if isinstance(argument.value, StringValueNode)
        ),
        "",
    ).startswith("https://specs.apollo.dev/federation")


def _is_nullable(field_type: TypeNode) -> bool:
    """Check if a field type is nullable (not wrapped in NonNullTypeNode)."""
    return not isinstance(field_type, NonNullTypeNode)


def _get_field_type(
    field_type: TypeNode,
    was_non_nullable: bool = False,
    *,
    wrap_in_maybe: bool = False,
) -> cst.BaseExpression:
    expr: cst.BaseExpression | None

    if isinstance(field_type, NonNullTypeNode):
        return _get_field_type(
            field_type.type, was_non_nullable=True, wrap_in_maybe=wrap_in_maybe
        )
    if isinstance(field_type, ListTypeNode):
        expr = cst.Subscript(
            value=cst.Name("list"),
            slice=[
                cst.SubscriptElement(
                    cst.Index(
                        value=_get_field_type(field_type.type),
                    ),
                )
            ],
        )
    elif isinstance(field_type, NamedTypeNode):
        expr = _SCALAR_MAP.get(field_type.name.value)

        if expr is None:
            expr = cst.Name(field_type.name.value)

    else:
        raise NotImplementedError(f"Unknown type {field_type}")

    if was_non_nullable:
        return expr

    nullable_expr = cst.BinaryOperation(
        left=expr,
        operator=cst.BitOr(),
        right=cst.Name("None"),
    )

    if wrap_in_maybe:
        return cst.Subscript(
            value=cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("Maybe"),
            ),
            slice=[
                cst.SubscriptElement(
                    cst.Index(value=nullable_expr),
                )
            ],
        )

    return nullable_expr


def _get_base_type_name(type_node: TypeNode) -> str:
    """Extract the base named type from a possibly wrapped type node."""
    if isinstance(type_node, (NonNullTypeNode, ListTypeNode)):
        return _get_base_type_name(type_node.type)

    if isinstance(type_node, NamedTypeNode):
        return type_node.name.value

    raise NotImplementedError(f"Unknown type node {type_node}")


def _get_default_value_expr(
    node: ConstValueNode,
    *,
    enum_type_name: str | None = None,
) -> cst.BaseExpression:
    """Convert a GraphQL default value AST node to a libcst expression."""
    if isinstance(node, IntValueNode):
        return cst.Integer(node.value)

    if isinstance(node, FloatValueNode):
        return cst.Float(node.value)

    if isinstance(node, StringValueNode):
        if '"' in node.value:
            return cst.SimpleString(f"'{node.value}'")

        return cst.SimpleString(f'"{node.value}"')

    if isinstance(node, BooleanValueNode):
        return cst.Name("True" if node.value else "False")

    if isinstance(node, NullValueNode):
        return cst.Name("None")

    if isinstance(node, EnumValueNode):
        if enum_type_name is None:
            raise ValueError("enum_type_name is required for EnumValueNode")

        return cst.Attribute(
            value=cst.Name(enum_type_name),
            attr=cst.Name(node.value),
        )

    if isinstance(node, ListValueNode):
        return cst.List(
            elements=[
                cst.Element(
                    value=_get_default_value_expr(v, enum_type_name=enum_type_name)
                )
                for v in node.values
            ]
        )

    raise NotImplementedError(f"Unknown default value node {node}")


def _sanitize_argument(
    value: ArgumentValue,
) -> cst.SimpleString | cst.Name | cst.List | cst.Integer | cst.Float:
    if isinstance(value, bool):
        return cst.Name(value=str(value))

    if value is None:
        return cst.Name(value="None")

    if isinstance(value, int):
        return cst.Integer(value=str(value))

    if isinstance(value, float):
        return cst.Float(value=str(value))

    if isinstance(value, list):
        return cst.List(
            elements=[
                cst.Element(value=_sanitize_argument(item))
                for item in value
                if item is not None
            ],
        )

    if "\n" in value:
        argument_value = cst.SimpleString(f'"""\n{value}\n"""')
    elif '"' in value:
        argument_value = cst.SimpleString(f"'{value}'")
    else:
        argument_value = cst.SimpleString(f'"{value}"')

    return argument_value


def _get_argument(name: str, value: ArgumentValue) -> cst.Arg:
    argument_value = _sanitize_argument(value)

    return cst.Arg(
        value=argument_value,
        keyword=cst.Name(name),
        equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
    )


def _get_field_value(
    field: FieldDefinitionNode | InputValueDefinitionNode,
    alias: str | None,
    is_apollo_federation: bool,
    imports: set[Import],
    *,
    default_value: cst.BaseExpression | None = None,
    directive_definitions: dict[str, str] | None = None,
) -> cst.Call | cst.BaseExpression | None:
    description = field.description.value if field.description else None

    args = list(
        filter(
            None,
            [
                _get_argument("description", description) if description else None,
                _get_argument("name", alias) if alias else None,
            ],
        )
    )

    directives = _get_directives(field)

    apollo_federation_args = _get_federation_arguments(directives, imports)

    if directive_definitions:
        non_fed_directives_arg = _get_non_federation_directives_arg(
            directives, directive_definitions
        )
        if non_fed_directives_arg is not None:
            args.append(non_fed_directives_arg)

    default_arg = (
        cst.Arg(
            value=default_value,
            keyword=cst.Name("default"),
            equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
        )
        if default_value is not None
        else None
    )

    if is_apollo_federation and apollo_federation_args:
        if default_arg is not None:
            args.append(default_arg)
        args.extend(apollo_federation_args)

        return cst.Call(
            func=cst.Attribute(
                value=cst.Attribute(
                    value=cst.Name("strawberry"),
                    attr=cst.Name("federation"),
                ),
                attr=cst.Name("field"),
            ),
            args=args,
        )

    if args:
        if default_arg is not None:
            args.append(default_arg)
        return cst.Call(
            func=cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("field"),
            ),
            args=args,
        )

    if default_value is not None:
        return default_value

    return None


def _get_field(
    field: FieldDefinitionNode | InputValueDefinitionNode,
    is_apollo_federation: bool,
    imports: set[Import],
    *,
    is_input_field: bool = False,
    directive_definitions: dict[str, str] | None = None,
) -> cst.SimpleStatementLine:
    name = to_snake_case(field.name.value)
    alias: str | None = None

    if keyword.iskeyword(name):
        name = f"{name}_"
        alias = field.name.value

    # For input types, wrap nullable fields in strawberry.Maybe[...]
    wrap_in_maybe = is_input_field and _is_nullable(field.type)

    # Extract default value for input fields
    default_value: cst.BaseExpression | None = None
    if isinstance(field, InputValueDefinitionNode) and field.default_value is not None:
        enum_type_name = (
            _get_base_type_name(field.type)
            if isinstance(field.default_value, EnumValueNode)
            else None
        )

        default_value = _get_default_value_expr(
            field.default_value, enum_type_name=enum_type_name
        )

    return cst.SimpleStatementLine(
        body=[
            cst.AnnAssign(
                target=cst.Name(name),
                annotation=cst.Annotation(
                    _get_field_type(field.type, wrap_in_maybe=wrap_in_maybe),
                ),
                value=_get_field_value(
                    field,
                    alias=alias,
                    is_apollo_federation=is_apollo_federation,
                    imports=imports,
                    default_value=default_value,
                    directive_definitions=directive_definitions,
                ),
            )
        ]
    )


ArgumentValue: TypeAlias = str | bool | int | float | None | list["ArgumentValue"]


def _get_argument_value(argument_value: ConstValueNode) -> ArgumentValue:
    if isinstance(argument_value, StringValueNode):
        return argument_value.value

    if isinstance(argument_value, EnumValueNode):
        return argument_value.value

    if isinstance(argument_value, ListValueNode):
        return [_get_argument_value(arg) for arg in argument_value.values]

    if isinstance(argument_value, BooleanValueNode):
        return argument_value.value

    if isinstance(argument_value, IntValueNode):
        return int(argument_value.value)

    if isinstance(argument_value, FloatValueNode):
        return float(argument_value.value)

    if isinstance(argument_value, NullValueNode):
        return None

    raise NotImplementedError(f"Unknown argument value {argument_value}")


def _get_directives(
    definition: HasDirectives,
) -> dict[str, list[dict[str, ArgumentValue]]]:
    directives: dict[str, list[dict[str, ArgumentValue]]] = defaultdict(list)

    for directive in definition.directives:
        directive_name = directive.name.value

        directives[directive_name].append(
            {
                argument.name.value: _get_argument_value(argument.value)
                for argument in directive.arguments
            }
        )

    return directives


def _get_federation_arguments(
    directives: dict[str, list[dict[str, ArgumentValue]]],
    imports: set[Import],
) -> list[cst.Arg]:
    def append_arg_from_directive(
        directive: str,
        argument_name: str,
        keyword_name: str | None = None,
        flatten: bool = True,
    ) -> None:
        keyword_name = keyword_name or directive

        if directive in directives:
            values = [item[argument_name] for item in directives[directive]]

            if flatten:
                arguments.append(_get_argument(keyword_name, values))
            else:
                arguments.extend(_get_argument(keyword_name, value) for value in values)

    arguments: list[cst.Arg] = []

    append_arg_from_directive("key", "fields", "keys")
    append_arg_from_directive("requires", "fields")
    append_arg_from_directive("provides", "fields")
    append_arg_from_directive(
        "requiresScopes", "scopes", "requires_scopes", flatten=False
    )
    append_arg_from_directive("policy", "policies", "policy", flatten=False)
    append_arg_from_directive("tag", "name", "tags")

    boolean_keys = (
        "shareable",
        "inaccessible",
        "external",
        "authenticated",
    )

    arguments.extend(
        _get_argument(key, True) for key in boolean_keys if directives.get(key, False)
    )

    if overrides := directives.get("override"):
        override = overrides[0]

        if "label" not in override:
            arguments.append(_get_argument("override", override["from"]))
        else:
            imports.add(
                Import(
                    module="strawberry.federation.schema_directives",
                    imports=("Override",),
                )
            )

            arguments.append(
                cst.Arg(
                    keyword=cst.Name("override"),
                    value=cst.Call(
                        func=cst.Name("Override"),
                        args=[
                            _get_argument("override_from", override["from"]),
                            _get_argument("label", override["label"]),
                        ],
                    ),
                    equal=cst.AssignEqual(
                        cst.SimpleWhitespace(""), cst.SimpleWhitespace("")
                    ),
                )
            )

    return arguments


def _get_non_federation_directives_arg(
    directives: dict[str, list[dict[str, ArgumentValue]]],
    directive_definitions: dict[str, str],
) -> cst.Arg | None:
    directive_calls: list[cst.Element] = []

    for directive_name, applications in directives.items():
        if directive_name not in directive_definitions:
            continue

        class_name = directive_definitions[directive_name]

        for application in applications:
            call_args = []
            for arg_name, arg_value in application.items():
                kwarg_name = to_snake_case(arg_name)
                if keyword.iskeyword(kwarg_name):
                    kwarg_name = f"{kwarg_name}_"
                call_args.append(
                    cst.Arg(
                        keyword=cst.Name(kwarg_name),
                        value=_sanitize_argument(arg_value),
                        equal=cst.AssignEqual(
                            cst.SimpleWhitespace(""), cst.SimpleWhitespace("")
                        ),
                    )
                )
            directive_calls.append(
                cst.Element(
                    value=cst.Call(
                        func=cst.Name(class_name),
                        args=call_args,
                    )
                )
            )

    if not directive_calls:
        return None

    return cst.Arg(
        keyword=cst.Name("directives"),
        value=cst.List(elements=directive_calls),
        equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
    )


def _get_strawberry_decorator(
    definition: ObjectTypeDefinitionNode
    | ObjectTypeExtensionNode
    | InterfaceTypeDefinitionNode
    | InputObjectTypeDefinitionNode,
    is_apollo_federation: bool,
    imports: set[Import],
    *,
    directive_definitions: dict[str, str] | None = None,
) -> cst.Decorator:
    type_ = {
        ObjectTypeDefinitionNode: "type",
        InterfaceTypeDefinitionNode: "interface",
        InputObjectTypeDefinitionNode: "input",
        ObjectTypeExtensionNode: "type",
    }[type(definition)]

    description = (
        definition.description
        if not isinstance(definition, ObjectTypeExtensionNode)
        else None
    )

    directives = _get_directives(definition)

    decorator: cst.BaseExpression = cst.Attribute(
        value=cst.Name("strawberry"),
        attr=cst.Name(type_),
    )

    arguments: list[cst.Arg] = []

    if description is not None:
        arguments.append(_get_argument("description", description.value))

    federation_arguments = _get_federation_arguments(directives, imports)

    # and has any directive that is a federation directive
    if is_apollo_federation and federation_arguments:
        decorator = cst.Attribute(
            value=cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("federation"),
            ),
            attr=cst.Name(type_),
        )

        arguments.extend(federation_arguments)

    if directive_definitions:
        non_fed_directives_arg = _get_non_federation_directives_arg(
            directives, directive_definitions
        )
        if non_fed_directives_arg is not None:
            arguments.append(non_fed_directives_arg)

    if arguments:
        decorator = cst.Call(
            func=decorator,
            args=arguments,
        )

    return cst.Decorator(
        decorator=decorator,
    )


def _get_class_definition(
    definition: ObjectTypeDefinitionNode
    | ObjectTypeExtensionNode
    | InterfaceTypeDefinitionNode
    | InputObjectTypeDefinitionNode,
    is_apollo_federation: bool,
    imports: set[Import],
    *,
    directive_definitions: dict[str, str] | None = None,
) -> Definition:
    decorator = _get_strawberry_decorator(
        definition,
        is_apollo_federation,
        imports,
        directive_definitions=directive_definitions,
    )

    interfaces = (
        [interface.name.value for interface in definition.interfaces]
        if isinstance(
            definition, (ObjectTypeDefinitionNode, InterfaceTypeDefinitionNode)
        )
        and definition.interfaces
        else []
    )

    is_input_type = isinstance(definition, InputObjectTypeDefinitionNode)

    class_definition = cst.ClassDef(
        name=cst.Name(definition.name.value),
        body=cst.IndentedBlock(
            body=[
                _get_field(
                    field,
                    is_apollo_federation,
                    imports,
                    is_input_field=is_input_type,
                    directive_definitions=directive_definitions,
                )
                for field in definition.fields
            ]
        ),
        bases=[cst.Arg(cst.Name(interface)) for interface in interfaces],
        decorators=[decorator],
    )

    dependencies = list(interfaces)

    if directive_definitions:
        type_directives = _get_directives(definition)
        for dir_name in type_directives:
            if dir_name in directive_definitions:
                cls = directive_definitions[dir_name]
                if cls not in dependencies:
                    dependencies.append(cls)

        for field in definition.fields:
            field_directives = _get_directives(field)
            for dir_name in field_directives:
                if dir_name in directive_definitions:
                    cls = directive_definitions[dir_name]
                    if cls not in dependencies:
                        dependencies.append(cls)

    return Definition(class_definition, dependencies, definition.name.value)


def _get_enum_value(enum_value: EnumValueDefinitionNode) -> cst.SimpleStatementLine:
    name = enum_value.name.value

    return cst.SimpleStatementLine(
        body=[
            cst.Assign(
                targets=[cst.AssignTarget(cst.Name(name))],
                value=cst.SimpleString(f'"{name}"'),
            )
        ]
    )


def _get_enum_definition(definition: EnumTypeDefinitionNode) -> Definition:
    decorator = cst.Decorator(
        decorator=cst.Attribute(
            value=cst.Name("strawberry"),
            attr=cst.Name("enum"),
        ),
    )

    class_definition = cst.ClassDef(
        name=cst.Name(definition.name.value),
        bases=[cst.Arg(cst.Name("Enum"))],
        body=cst.IndentedBlock(
            body=[_get_enum_value(value) for value in definition.values]
        ),
        decorators=[decorator],
    )

    return Definition(
        class_definition,
        [],
        definition.name.value,
    )


def _get_schema_definition(
    root_query_name: str | None,
    root_mutation_name: str | None,
    root_subscription_name: str | None,
    is_apollo_federation: bool,
) -> cst.SimpleStatementLine | None:
    if not any([root_query_name, root_mutation_name, root_subscription_name]):
        return None

    args: list[cst.Arg] = []

    def _get_arg(name: str, value: str) -> cst.Arg:
        return cst.Arg(
            keyword=cst.Name(name),
            value=cst.Name(value),
            equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
        )

    if root_query_name:
        args.append(_get_arg("query", root_query_name))

    if root_mutation_name:
        args.append(_get_arg("mutation", root_mutation_name))

    if root_subscription_name:
        args.append(_get_arg("subscription", root_subscription_name))

    # Federation 2 is now always enabled for federation schemas
    if is_apollo_federation:
        schema_call = cst.Call(
            func=cst.Attribute(
                value=cst.Attribute(
                    value=cst.Name(value="strawberry"),
                    attr=cst.Name(value="federation"),
                ),
                attr=cst.Name(value="Schema"),
            ),
            args=args,
        )
    else:
        schema_call = cst.Call(
            func=cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("Schema"),
            ),
            args=args,
        )

    return cst.SimpleStatementLine(
        body=[
            cst.Assign(
                targets=[cst.AssignTarget(cst.Name("schema"))],
                value=schema_call,
            )
        ]
    )


@dataclasses.dataclass(frozen=True)
class Definition:
    code: cst.CSTNode
    dependencies: list[str]
    name: str


def _get_union_definition(definition: UnionTypeDefinitionNode) -> Definition:
    name = definition.name.value

    types = cst.parse_expression(
        " | ".join([type_.name.value for type_ in definition.types])
    )

    simple_statement = cst.SimpleStatementLine(
        body=[
            cst.Assign(
                targets=[cst.AssignTarget(cst.Name(name))],
                value=cst.Subscript(
                    value=cst.Name("Annotated"),
                    slice=[
                        cst.SubscriptElement(slice=cst.Index(types)),
                        cst.SubscriptElement(
                            slice=cst.Index(
                                cst.Call(
                                    cst.Attribute(
                                        value=cst.Name("strawberry"),
                                        attr=cst.Name("union"),
                                    ),
                                    args=[_get_argument("name", name)],
                                )
                            )
                        ),
                    ],
                ),
            )
        ]
    )
    return Definition(
        simple_statement,
        [],
        definition.name.value,
    )


def _get_scalar_definition(
    definition: ScalarTypeDefinitionNode, imports: set[Import]
) -> Definition | None:
    name = definition.name.value

    if name == "Date":
        imports.add(Import(module="datetime", imports=("date",)))
        return None
    if name == "Time":
        imports.add(Import(module="datetime", imports=("time",)))
        return None
    if name == "DateTime":
        imports.add(Import(module="datetime", imports=("datetime",)))
        return None
    if name == "Decimal":
        imports.add(Import(module="decimal", imports=("Decimal",)))
        return None
    if name == "UUID":
        imports.add(Import(module="uuid", imports=("UUID",)))
        return None
    if name == "JSON":
        return None

    description = definition.description.value if definition.description else None

    specified_by_url = None

    for directive in definition.directives:
        if directive.name.value == "specifiedBy":
            arg = directive.arguments[0]

            assert isinstance(arg.value, StringValueNode)

            specified_by_url = arg.value.value

    imports.add(Import(module="typing", imports=("NewType",)))

    identity_lambda = cst.Lambda(
        body=cst.Name("v"),
        params=cst.Parameters(
            params=[cst.Param(cst.Name("v"))],
        ),
    )

    additional_args: list[cst.Arg | None] = [
        _get_argument("description", description) if description else None,
        _get_argument("specified_by_url", specified_by_url)
        if specified_by_url
        else None,
        cst.Arg(
            keyword=cst.Name("serialize"),
            value=identity_lambda,
            equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
        ),
        cst.Arg(
            keyword=cst.Name("parse_value"),
            value=identity_lambda,
            equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
        ),
    ]

    statement_definition = cst.SimpleStatementLine(
        body=[
            cst.Assign(
                targets=[cst.AssignTarget(cst.Name(name))],
                value=cst.Call(
                    func=cst.Attribute(
                        value=cst.Name("strawberry"),
                        attr=cst.Name("scalar"),
                    ),
                    args=[
                        cst.Arg(
                            cst.Call(
                                func=cst.Name("NewType"),
                                args=[
                                    cst.Arg(cst.SimpleString(f'"{name}"')),
                                    cst.Arg(cst.Name("object")),
                                ],
                            )
                        ),
                        *filter(None, additional_args),
                    ],
                ),
            )
        ]
    )
    return Definition(statement_definition, [], name=definition.name.value)


def _get_directive_definition(
    definition: DirectiveDefinitionNode,
    imports: set[Import],
) -> Definition | None:
    name = definition.name.value

    if name in _FEDERATION_DIRECTIVE_NAMES:
        return None

    class_name = capitalize_first(name)

    locations = [
        loc.value
        for loc in definition.locations
        if loc.value in _STRAWBERRY_LOCATION_NAMES
    ]

    if not locations:
        return None

    location_elements = [
        cst.Element(
            value=cst.Attribute(
                value=cst.Name("Location"),
                attr=cst.Name(loc),
            )
        )
        for loc in locations
    ]

    decorator_args: list[cst.Arg] = []

    if definition.description:
        decorator_args.append(
            _get_argument("description", definition.description.value)
        )

    decorator_args.append(
        cst.Arg(
            keyword=cst.Name("locations"),
            value=cst.List(elements=location_elements),
            equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
        )
    )

    if definition.repeatable:
        decorator_args.append(
            cst.Arg(
                keyword=cst.Name("repeatable"),
                value=cst.Name("True"),
                equal=cst.AssignEqual(
                    cst.SimpleWhitespace(""), cst.SimpleWhitespace("")
                ),
            )
        )

    decorator = cst.Decorator(
        decorator=cst.Call(
            func=cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("schema_directive"),
            ),
            args=decorator_args,
        ),
    )

    dependencies: list[str] = []
    body_lines: list[cst.BaseStatement] = []

    if definition.arguments:
        for arg in definition.arguments:
            arg_name = to_snake_case(arg.name.value)
            alias: str | None = None

            if keyword.iskeyword(arg_name):
                arg_name = f"{arg_name}_"
                alias = arg.name.value
            elif arg_name != arg.name.value:
                alias = arg.name.value

            field_type_expr = _get_field_type(arg.type)

            base_type = _get_base_type_name(arg.type)
            if base_type not in _SCALAR_MAP:
                dependencies.append(base_type)

            default_value: cst.BaseExpression | None = None
            if arg.default_value is not None:
                enum_type_name = (
                    _get_base_type_name(arg.type)
                    if isinstance(arg.default_value, EnumValueNode)
                    else None
                )
                default_value = _get_default_value_expr(
                    arg.default_value, enum_type_name=enum_type_name
                )

            field_value: cst.BaseExpression | None = None
            if alias is not None:
                directive_field_args: list[cst.Arg] = [
                    _get_argument("name", alias),
                ]
                if default_value is not None:
                    directive_field_args.append(
                        cst.Arg(
                            keyword=cst.Name("default"),
                            value=default_value,
                            equal=cst.AssignEqual(
                                cst.SimpleWhitespace(""), cst.SimpleWhitespace("")
                            ),
                        )
                    )
                field_value = cst.Call(
                    func=cst.Attribute(
                        value=cst.Name("strawberry"),
                        attr=cst.Name("directive_field"),
                    ),
                    args=directive_field_args,
                )
            elif default_value is not None:
                field_value = default_value

            body_lines.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.AnnAssign(
                            target=cst.Name(arg_name),
                            annotation=cst.Annotation(field_type_expr),
                            value=field_value,
                        )
                    ]
                )
            )

    if not body_lines:
        body_lines.append(
            cst.SimpleStatementLine(body=[cst.Expr(cst.Name("pass"))])
        )

    class_definition = cst.ClassDef(
        name=cst.Name(class_name),
        body=cst.IndentedBlock(body=body_lines),
        decorators=[decorator],
    )

    imports.add(Import(module="strawberry.schema_directive", imports=("Location",)))

    return Definition(class_definition, dependencies, class_name)


def codegen(schema: str) -> str:
    document = parse(schema)

    definitions: dict[str, Definition] = {}

    root_query_name: str | None = None
    root_mutation_name: str | None = None
    root_subscription_name: str | None = None

    imports: set[Import] = {
        Import(module=None, imports=("strawberry",)),
    }

    # Pre-scan for directive definitions to build name mapping
    directive_definitions: dict[str, str] = {}
    for graphql_definition in document.definitions:
        if isinstance(graphql_definition, DirectiveDefinitionNode):
            name = graphql_definition.name.value
            if name not in _FEDERATION_DIRECTIVE_NAMES:
                has_type_system_location = any(
                    loc.value in _STRAWBERRY_LOCATION_NAMES
                    for loc in graphql_definition.locations
                )
                if has_type_system_location:
                    directive_definitions[name] = capitalize_first(name)

    # when we encounter a extend schema @link ..., we check if is an apollo federation schema
    # and we use this variable to keep track of it, but at the moment the assumption is that
    # the schema extension is always done at the top, this might not be the case all the
    # time
    is_apollo_federation = False

    for graphql_definition in document.definitions:
        definition: Definition | None = None

        if isinstance(
            graphql_definition,
            (
                ObjectTypeDefinitionNode,
                InterfaceTypeDefinitionNode,
                InputObjectTypeDefinitionNode,
                ObjectTypeExtensionNode,
            ),
        ):
            definition = _get_class_definition(
                graphql_definition,
                is_apollo_federation,
                imports,
                directive_definitions=directive_definitions,
            )

        elif isinstance(graphql_definition, EnumTypeDefinitionNode):
            imports.add(Import(module="enum", imports=("Enum",)))

            definition = _get_enum_definition(graphql_definition)

        elif isinstance(graphql_definition, SchemaDefinitionNode):
            for operation_type_definition in graphql_definition.operation_types:
                if operation_type_definition.operation == OperationType.QUERY:
                    root_query_name = operation_type_definition.type.name.value
                elif operation_type_definition.operation == OperationType.MUTATION:
                    root_mutation_name = operation_type_definition.type.name.value
                elif operation_type_definition.operation == OperationType.SUBSCRIPTION:
                    root_subscription_name = operation_type_definition.type.name.value
                else:
                    raise NotImplementedError(
                        f"Unknown operation {operation_type_definition.operation}"
                    )
        elif isinstance(graphql_definition, UnionTypeDefinitionNode):
            imports.add(Import(module="typing", imports=("Annotated",)))

            definition = _get_union_definition(graphql_definition)
        elif isinstance(graphql_definition, ScalarTypeDefinitionNode):
            definition = _get_scalar_definition(graphql_definition, imports)

        elif isinstance(graphql_definition, SchemaExtensionNode):
            is_apollo_federation = any(
                _is_federation_link_directive(directive)
                for directive in graphql_definition.directives
            )
        elif isinstance(graphql_definition, DirectiveDefinitionNode):
            definition = _get_directive_definition(graphql_definition, imports)
        else:
            raise NotImplementedError(f"Unknown definition {definition}")

        if definition is not None:
            definitions[definition.name] = definition

    if root_query_name is None:
        root_query_name = "Query" if "Query" in definitions else None

    if root_mutation_name is None:
        root_mutation_name = "Mutation" if "Mutation" in definitions else None

    if root_subscription_name is None:
        root_subscription_name = (
            "Subscription" if "Subscription" in definitions else None
        )

    schema_definition = _get_schema_definition(
        root_query_name=root_query_name,
        root_mutation_name=root_mutation_name,
        root_subscription_name=root_subscription_name,
        is_apollo_federation=is_apollo_federation,
    )

    if schema_definition:
        definitions["Schema"] = Definition(schema_definition, [], "schema")

    body: list[cst.CSTNode] = [
        cst.SimpleStatementLine(body=[import_.to_cst()])
        for import_ in sorted(imports, key=lambda i: (i.module or "", i.imports))
    ]

    # DAG to sort definitions based on dependencies
    graph = {name: definition.dependencies for name, definition in definitions.items()}
    ts = TopologicalSorter(graph)

    for definition_name in tuple(ts.static_order()):
        definition = definitions[definition_name]

        body.append(cst.EmptyLine())
        body.append(definition.code)

    module = cst.Module(body=body)  # type: ignore

    return module.code


__all__ = ["codegen"]
