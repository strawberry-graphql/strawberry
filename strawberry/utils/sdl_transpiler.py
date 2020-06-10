"""
### SDL Transpiler
This module contains functions designed to parse GraphQL SDL to AST and transpile AST
to valid strawberry data class strings.
The file printing is left to the caller which received input and output arguments.
"""
from jinja2 import Template
from .str_converters import to_snake_case

# Simple Jinja2 template string for generating valid strawberry class
TEMPLATE = """{{ get_decorator(ast.kind) }}{{ get_description(ast) }}
class {{ get_class_name(ast) }}:
    {%- for field in ast.fields %}
    {{ get_field_attribute(field) }}
    {%- endfor %}
"""

# QUESTION: Is there a beeter way to determine this?
SCALAR_TYPES = {
    "Int": "int",
    "Float": "float",
    "String": "str",
    "Boolean": "bool",
    "ID": "strawberry.ID",
}

# Base decorator kinds
DECORATOR_KINDS = {
    "schema_definition": "@strawberry.type",
    "object_type_definition": "@strawberry.type",
    "enum_type_definition": "@strawberry.enum",
    "union_type_definition": "@strawberry.union",
    "interface_type_definition": "@strawberry.interface",
    "input_type_definition": "@strawberry.input",
}


def get_class_name(ast):
    return "Schema" if ast.kind == "schema_definition" else ast.name.value


def get_decorator(kind):
    """ Creates and returns decorator string """
    return DECORATOR_KINDS[kind]


def get_description(ast):
    """ Creates and returns decorator string """
    if not hasattr(ast, "description") or ast.description is None:
        return ""
    else:
        return f"(description='''{ast.description.value}''')"


def get_field_attribute(field):
    field_name = to_snake_case(field.name.value)
    field_type = get_field_type(field)
    strawberry_type = get_strawberry_type(
        "" if field.name.value == field_name else field.name.value, field.description
    )
    sufix = ""
    if field.type.kind != "non_null_type":
        sufix = " = None"
    field_type += strawberry_type if strawberry_type else sufix
    return f"{field_name}: {field_type}"


def get_field_type(field, optional=True):
    """ Go down the tree to find out the type of field """
    if field.type.kind == "list_type":
        field_type = "typing.List[{}]".format(get_field_type(field.type))

    elif field.type.kind == "non_null_type":
        field_type = "{}".format(get_field_type(field.type, optional=False))

    else:
        base_field = "typing.Optional[{}]" if optional else "{}"
        base_type = (
            SCALAR_TYPES[field.type.name.value]
            if field.type.name.value in SCALAR_TYPES
            else field.type.name.value
        )
        return base_field.format(base_type)

    return field_type


def get_strawberry_type(name, description):
    strawberry_type = ""
    if name or description is not None:
        strawberry_type = " = strawberry.field({}{}    )".format(
            f"\n        name='{name}'," if name else "",
            f"\n        description='''{description.value}'''\n"
            if description is not None
            else "",
        )
    return strawberry_type


def render_template(ast):
    """ Populates templates based on type of graphql object definition """
    template = Template(TEMPLATE)
    output = template.render(
        get_field_attribute=get_field_attribute,
        get_description=get_description,
        get_decorator=get_decorator,
        get_class_name=get_class_name,
        ast=ast,
    )
    return output
