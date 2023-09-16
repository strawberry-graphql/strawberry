from __future__ import annotations

import keyword

import libcst as cst
from graphql import (
    FieldDefinitionNode,
    InterfaceTypeDefinitionNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    ObjectTypeDefinitionNode,
    OperationType,
    SchemaDefinitionNode,
    TypeNode,
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
}


def _get_field_type(
    field_type: TypeNode, was_non_nullable: bool = False
) -> cst.BaseExpression:
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


def _get_field(field: FieldDefinitionNode) -> cst.SimpleStatementLine:
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
    definition: ObjectTypeDefinitionNode | InterfaceTypeDefinitionNode,
) -> cst.Decorator:
    type_ = {
        ObjectTypeDefinitionNode: "type",
        InterfaceTypeDefinitionNode: "interface",
    }[type(definition)]

    description = definition.description

    decorator = cst.Attribute(
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
    definition: ObjectTypeDefinitionNode | InterfaceTypeDefinitionNode,
) -> cst.ClassDef:
    decorator = _get_strawberry_decorator(definition)

    bases = (
        [cst.Arg(cst.Name(interface.name.value)) for interface in definition.interfaces]
        if definition.interfaces
        else []
    )

    return cst.ClassDef(
        name=cst.Name(definition.name.value),
        bases=bases,
        body=cst.IndentedBlock(body=[_get_field(field) for field in definition.fields]),
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


def codegen(schema: str) -> str:
    document = parse(schema)

    definitions: list[cst.CSTNode] = []

    root_query_name: str | None = None
    root_mutation_name: str | None = None
    root_subscription_name: str | None = None

    for definition in document.definitions:
        definitions.append(cst.EmptyLine())  # type: ignore - this works :)

        if isinstance(
            definition, (ObjectTypeDefinitionNode, InterfaceTypeDefinitionNode)
        ):
            class_definition = _get_class_definition(definition)

            definitions.append(class_definition)
        elif isinstance(definition, SchemaDefinitionNode):
            for operation_type_definition in definition.operation_types:
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
        else:
            raise NotImplementedError(f"Unknown definition {definition}")

    schema_definition = _get_schema_definition(
        root_query_name=root_query_name,
        root_mutation_name=root_mutation_name,
        root_subscription_name=root_subscription_name,
    )

    if schema_definition:
        definitions.append(schema_definition)

    module = cst.Module(
        body=[
            cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("strawberry"))])]
            ),
            *definitions,  # type: ignore
        ]
    )

    return module.code
