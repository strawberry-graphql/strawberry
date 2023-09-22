from __future__ import annotations

import dataclasses
import keyword

import libcst as cst
from graphlib import TopologicalSorter
from graphql import (
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
    StringValueNode,
    TypeNode,
    UnionTypeDefinitionNode,
    parse,
)

from strawberry.utils.str_converters import to_snake_case

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


def _get_field_type(
    field_type: TypeNode, was_non_nullable: bool = False
) -> cst.BaseExpression:
    expr: cst.BaseExpression | None

    if isinstance(field_type, NonNullTypeNode):
        return _get_field_type(field_type.type, was_non_nullable=True)
    elif isinstance(field_type, ListTypeNode):
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

    return cst.BinaryOperation(
        left=expr,
        operator=cst.BitOr(),
        right=cst.Name("None"),
    )


def _get_argument(name: str, value: str) -> cst.Arg:
    if "\n" in value:
        argument_value = cst.SimpleString(f'"""\n{value}\n"""')
    elif '"' in value:
        argument_value = cst.SimpleString(f"'{value}'")
    else:
        argument_value = cst.SimpleString(f'"{value}"')

    return cst.Arg(
        value=argument_value,
        keyword=cst.Name(name),
        equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
    )


def _get_field_value(description: str | None, alias: str | None) -> cst.Call | None:
    args = list(
        filter(
            None,
            [
                _get_argument("description", description) if description else None,
                _get_argument("name", alias) if alias else None,
            ],
        )
    )

    if args:
        return cst.Call(
            func=cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("field"),
            ),
            args=args,
        )

    return None


def _get_field(
    field: FieldDefinitionNode | InputValueDefinitionNode,
) -> cst.SimpleStatementLine:
    name = to_snake_case(field.name.value)
    alias: str | None = None

    if keyword.iskeyword(name):
        name = f"{name}_"
        alias = field.name.value

    return cst.SimpleStatementLine(
        body=[
            cst.AnnAssign(
                target=cst.Name(name),
                annotation=cst.Annotation(
                    _get_field_type(field.type),
                ),
                value=_get_field_value(
                    description=field.description.value if field.description else None,
                    alias=alias if alias != name else None,
                ),
            )
        ]
    )


def _get_strawberry_decorator(
    definition: ObjectTypeDefinitionNode
    | ObjectTypeExtensionNode
    | InterfaceTypeDefinitionNode
    | InputObjectTypeDefinitionNode,
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

    decorator: cst.BaseExpression = cst.Attribute(
        value=cst.Name("strawberry"),
        attr=cst.Name(type_),
    )

    if description is not None:
        decorator = cst.Call(
            func=decorator,
            args=[_get_argument("description", description.value)],
        )

    return cst.Decorator(
        decorator=decorator,
    )


def _get_class_definition(
    definition: ObjectTypeDefinitionNode
    | ObjectTypeExtensionNode
    | InterfaceTypeDefinitionNode
    | InputObjectTypeDefinitionNode,
) -> Definition:
    decorator = _get_strawberry_decorator(definition)

    interfaces = (
        [interface.name.value for interface in definition.interfaces]
        if isinstance(
            definition, (ObjectTypeDefinitionNode, InterfaceTypeDefinitionNode)
        )
        and definition.interfaces
        else []
    )

    class_definition = cst.ClassDef(
        name=cst.Name(definition.name.value),
        bases=[cst.Arg(cst.Name(interface)) for interface in interfaces],
        body=cst.IndentedBlock(body=[_get_field(field) for field in definition.fields]),
        decorators=[decorator],
    )

    return Definition(class_definition, interfaces, definition.name.value)


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


def _get_enum_definition(definition: EnumTypeDefinitionNode) -> cst.ClassDef:
    decorator = cst.Decorator(
        decorator=cst.Attribute(
            value=cst.Name("strawberry"),
            attr=cst.Name("enum"),
        ),
    )

    return cst.ClassDef(
        name=cst.Name(definition.name.value),
        bases=[cst.Arg(cst.Name("Enum"))],
        body=cst.IndentedBlock(
            body=[_get_enum_value(value) for value in definition.values]
        ),
        decorators=[decorator],
    )


def _get_schema_definition(
    root_query_name: str | None,
    root_mutation_name: str | None,
    root_subscription_name: str | None,
) -> cst.SimpleStatementLine | None:
    if not any([root_query_name, root_mutation_name, root_subscription_name]):
        return None

    args: list[cst.Arg] = []

    def _get_arg(name: str, value: str):
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

    return cst.SimpleStatementLine(
        body=[
            cst.Assign(
                targets=[cst.AssignTarget(cst.Name("schema"))],
                value=cst.Call(
                    func=cst.Attribute(
                        value=cst.Name("strawberry"),
                        attr=cst.Name("Schema"),
                    ),
                    args=args,
                ),
            )
        ]
    )


@dataclasses.dataclass(frozen=True)
class Import:
    module: str | None
    imports: tuple[str]

    def to_cst(self) -> cst.Import | cst.ImportFrom:
        if self.module is None:
            return cst.Import(
                names=[cst.ImportAlias(name=cst.Name(name)) for name in self.imports]
            )

        return cst.ImportFrom(
            module=cst.Name(self.module),
            names=[cst.ImportAlias(name=cst.Name(name)) for name in self.imports],
        )


@dataclasses.dataclass(frozen=True)
class Definition:
    code: cst.CSTNode
    dependencies: list[str]
    name: str


def _get_union_definition(
    definition: UnionTypeDefinitionNode,
) -> cst.SimpleStatementLine:
    name = definition.name.value

    types = cst.parse_expression(
        " | ".join([type_.name.value for type_ in definition.types])
    )

    return cst.SimpleStatementLine(
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


def _get_scalar_definition(
    definition: ScalarTypeDefinitionNode, imports: set[Import]
) -> cst.SimpleStatementLine | None:
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

    return cst.SimpleStatementLine(
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


def codegen(schema: str) -> str:
    document = parse(schema)

    # TODO: check if we can have the same name for multiple things
    definitions: dict[str, Definition] = {}

    root_query_name: str | None = None
    root_mutation_name: str | None = None
    root_subscription_name: str | None = None

    imports: set[Import] = {
        Import(module=None, imports=("strawberry",)),
    }

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
            definition = _get_class_definition(graphql_definition)

        elif isinstance(graphql_definition, EnumTypeDefinitionNode):
            imports.add(Import(module="enum", imports=("Enum",)))

            definition = Definition(
                _get_enum_definition(graphql_definition),
                [],
                graphql_definition.name.value,
            )

        elif isinstance(graphql_definition, UnionTypeDefinitionNode):
            imports.add(Import(module="typing", imports=("Annotated",)))

            definition = Definition(
                _get_union_definition(graphql_definition),
                [],
                graphql_definition.name.value,
            )

        elif isinstance(graphql_definition, ScalarTypeDefinitionNode):
            scalar_definition = _get_scalar_definition(graphql_definition, imports)

            if scalar_definition is not None:
                definition = Definition(
                    scalar_definition, [], name=graphql_definition.name.value
                )
            else:
                continue
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

            continue

        if definition is not None:
            definitions[definition.name] = definition

        else:
            raise NotImplementedError(f"Unknown definition {definition}")

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
    )

    if schema_definition:
        definitions["Schema"] = Definition(schema_definition, [], "schema")

    body = [
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

    module = cst.Module(body=body)

    return module.code
