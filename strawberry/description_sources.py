from enum import Flag, auto


class DescriptionSources(Flag):
    """
    A possible source of the GraphQL description fields.

    By default, strawberry only uses explicitly defined descriptions
    (STRAWBERRY_DESCRIPTIONS), but it is also possible to use docstrings
    at the class level, at each resolver methods, class attributes, etc.
    """

    NONE = 0

    STRAWBERRY_DESCRIPTIONS = auto()  # e.g., strawberry.type(description="...")

    RESOLVER_DOCSTRINGS = auto()

    TYPE_DOCSTRINGS = auto()
    ENUM_DOCSTRINGS = auto()
    DIRECTIVE_DOCSTRINGS = auto()
    CLASS_DOCSTRINGS = TYPE_DOCSTRINGS | ENUM_DOCSTRINGS | DIRECTIVE_DOCSTRINGS

    TYPE_ATTRIBUTE_DOCSTRINGS = auto()  # Using PEP 257 syntax
    ENUM_ATTRIBUTE_DOCSTRINGS = auto()  # Using PEP 257 syntax
    DIRECTIVE_ATTRIBUTE_DOCSTRINGS = auto()  # Using PEP 257 syntax
    ATTRIBUTE_DOCSTRINGS = (
        TYPE_ATTRIBUTE_DOCSTRINGS
        | ENUM_ATTRIBUTE_DOCSTRINGS
        | DIRECTIVE_ATTRIBUTE_DOCSTRINGS
    )

    ALL_DOCSTRINGS = RESOLVER_DOCSTRINGS | CLASS_DOCSTRINGS | ATTRIBUTE_DOCSTRINGS

    ALL = STRAWBERRY_DESCRIPTIONS | ALL_DOCSTRINGS
