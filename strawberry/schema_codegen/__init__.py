from __future__ import annotations

import libcst as cst
from graphql import (
    FieldDefinitionNode,
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
            raise NotImplementedError(f"Unknown type {field_type.name.value}")

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
    return cst.Arg(
        value=cst.SimpleString(f'"{value}"'),
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
    definition: ObjectTypeDefinitionNode,
) -> cst.Decorator:
    type_ = "type"

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


def codegen(schema: str) -> str:
    document = parse(schema)

    definitions: list[cst.BaseCompoundStatement] = []

    for definition in document.definitions:
        assert isinstance(definition, ObjectTypeDefinitionNode)

        decorator = _get_strawberry_decorator(definition)

        class_definition = cst.ClassDef(
            name=cst.Name(definition.name.value),
            bases=[],
            body=cst.IndentedBlock(
                body=[_get_field(field) for field in definition.fields]
            ),
            decorators=[decorator],
        )

        definitions.append(class_definition)

    module = cst.Module(
        body=[
            cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("strawberry"))])]
            ),
            cst.EmptyLine(),  # type: ignore - this works :)
            *definitions,
        ]
    )

    return module.code
