from __future__ import annotations

import libcst as cst
from graphql import (
    FieldDefinitionNode,
    InterfaceTypeDefinitionNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    ObjectTypeDefinitionNode,
    TypeNode,
    parse,
)

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
        keyword=cst.Name("description"),
        equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace("")),
    )


def _get_field(field: FieldDefinitionNode) -> cst.SimpleStatementLine:
    if field.description:
        value = cst.Call(
            func=cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("field"),
            ),
            args=[_get_argument("description", field.description.value)],
        )
    else:
        value = None

    return cst.SimpleStatementLine(
        body=[
            cst.AnnAssign(
                target=cst.Name(field.name.value),
                annotation=cst.Annotation(
                    _get_field_type(field.type),
                ),
                value=value,
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


def codegen(schema: str) -> str:
    document = parse(schema)

    definitions: list[cst.BaseCompoundStatement] = []

    for definition in document.definitions:
        definitions.append(cst.EmptyLine())  # type: ignore - this works :)

        if isinstance(
            definition, (ObjectTypeDefinitionNode, InterfaceTypeDefinitionNode)
        ):
            class_definition = _get_class_definition(definition)

            definitions.append(class_definition)
        else:
            raise NotImplementedError(f"Unknown definition {definition}")

    module = cst.Module(
        body=[
            cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("strawberry"))])]
            ),
            *definitions,
        ]
    )

    return module.code
