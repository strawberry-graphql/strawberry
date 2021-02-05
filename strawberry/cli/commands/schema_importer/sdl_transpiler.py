"""
### SDL Transpiler
This module contains functions designed to parse GraphQL SDL to AST and transpile AST
to valid strawberry data class strings.
The file printing is left to the caller which received input and output arguments.
"""

from jinja2 import Template

from strawberry.utils import str_converters


# Jinja2 templates
# strawberry class
TEMPLATE = """{{ decorator + description }}
class {{ class_name }}:
    {%- if ast.kind in standard_types -%}
    {%- for field in ast.fields %}
    {{ get_field_attribute(field) }}
    {%- endfor %}
    {%- endif -%}
    {%- if ast.kind == 'enum_type_definition' -%}
    {%- for value in ast.values %}
    {{ value.name.value }} = '{{ value.name.value.lower() }}'
    {%- endfor %}
    {%- endif -%}
"""

# strawberry union definitions
UNION_TEMPLATE = """{{ class_name }} = {{ get_union(ast) }}"""

# strawberry directives
# TODO: How do i know which type should first arg(value) be ?
DIRECTIVE_TEMPLATE = """@strawberry.directive(
    locations=[
        {%- for field in ast.locations %}
        DirectiveLocation.{{ field.value }}
        {%- endfor %}
    ],
{% if description -%}{{ '    ' + description[1:-1] + '\n' }}{%- endif -%}
)
def {{ class_name }}(
    {%- for field in ast.arguments %}
    {{ get_field_attribute(field) }}
    {%- endfor %}
):
    pass
"""

# QUESTION: Is there a better way to determine this?
SCALAR_TYPES = {
    "Int": "int",
    "String": "str",
    "Float": "float",
    "Boolean": "bool",
    "ID": "strawberry.ID",
}

# Base decorator kinds
DECORATOR_KINDS = {
    "union_type_definition": "",
    "schema_definition": "@strawberry.type",
    "enum_type_definition": "@strawberry.enum",
    "object_type_definition": "@strawberry.type",
    "directive_definition": "@strawberry.directive",
    "input_object_type_definition": "@strawberry.input",
    "interface_type_definition": "@strawberry.interface",
}


def get_class_name(ast):
    name = "Schema" if ast.kind == "schema_definition" else ast.name.value
    name += "(Enum)" if ast.kind == "enum_type_definition" else ""
    return name


def get_decorator(ast):
    """ Creates and returns decorator string """
    return DECORATOR_KINDS[ast.kind]


def get_description(ast):
    """ Creates and returns decorator string """
    if not hasattr(ast, "description") or ast.description is None:
        return ""
    else:
        return f"(description='''{ast.description.value}''')"


def get_directive(ast):
    """ Format union type """
    types = "(" + ", ".join((t.name.value for t in ast.types)) + ")"
    description = get_description(ast)
    description = f"{description[1:-1]}" if description else ""
    union_type = "strawberry.union({}{}{})".format(
        f"\n    '{get_class_name(ast)}',",
        f"\n    {types},",
        f"\n    {description}\n" if description else "\n",
    )

    return union_type


def get_union(ast):
    """ Format union type """
    types = "(" + ", ".join((t.name.value for t in ast.types)) + ")"
    description = get_description(ast)
    description = f"{description[1:-1]}" if description else ""
    union_type = "strawberry.union({}{}{})".format(
        f"\n    '{get_class_name(ast)}',",
        f"\n    {types},",
        f"\n    {description}\n" if description else "\n",
    )

    return union_type


def get_field_attribute(field):
    """
    Format and return a whole attribute string
    consists of attribute name in snake case and field type
    """
    field_name = get_field_name(field.name.value)
    field_type = get_field_type(field)
    strawberry_type = get_strawberry_type(
        field_name, field.description, field.directives
    )
    field_type += strawberry_type if strawberry_type else ""
    return f"{str_converters.to_snake_case(field.name.value)}: {field_type}"


def get_field_name(field_name):
    """ Check if name attribute Extract field name """
    snake_name = str_converters.to_snake_case(field_name)
    camel_name = str_converters.to_camel_case(field_name)
    if camel_name == snake_name or camel_name == field_name:
        return ""
    else:
        return field_name


def get_field_type(field, optional=True):
    """ Go down the tree to find out the type of field """
    if field.type.kind == "list_type":
        field_type = "typing.List[{}]".format(get_field_type(field.type))
        field_type = f"typing.Optional[{field_type}]" if optional else field_type

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


def get_strawberry_type(name, description, directives):
    """ Create strawberry type field as a string """
    strawberry_type = ""
    deprecated = [d for d in directives if d.name.value == "deprecated"]
    deprecated = deprecated[0] if deprecated else None
    if name or description is not None or directives or deprecated:
        strawberry_type = " = strawberry.field({}{}{}    )".format(
            f"\n        name='{name}'," if name else "",
            f"\n        description='''{description.value}''',\n"
            if description is not None
            else "",
            f"\n        derpecation_reason='{deprecated.arguments[0].value.value}',\n"
            if deprecated
            else "",
        )
    return strawberry_type


def get_template(ast):
    if ast.kind == "directive_definition":
        t = DIRECTIVE_TEMPLATE
    elif ast.kind == "union_type_definition":
        t = UNION_TEMPLATE
    else:
        t = TEMPLATE

    return Template(t)


def transpile(ast):
    """ Populates templates based on type of graphql object definition """
    template = get_template(ast)
    output = template.render(
        decorator=get_decorator(ast),
        class_name=get_class_name(ast),
        description=get_description(ast),
        get_union=get_union,
        get_field_attribute=get_field_attribute,
        standard_types=[
            "object_type_definition",
            "input_object_type_definition",
            "interface_type_definition",
        ],
        ast=ast,
    )
    return output[1:] if output.startswith("\n") else output
