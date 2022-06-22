from enum import Enum, auto


class DescriptionSource(Enum):
    """
    A possible source of the GraphQL description fields.

    By default, strawberry only uses explicitly defined descriptions
    (STRAWBERRY_DESCRIPTIONS), but it is also possible to use docstrings
    """

    STRAWBERRY_DESCRIPTIONS = auto()  # e.g., strawberry.type(description="...")
    RESOLVER_DOCSTRINGS = auto()
    DIRECTIVE_DOCSTRINGS = auto()
    TYPE_DOCSTRINGS = auto()
    ENUM_DOCSTRINGS = auto()
    TYPE_ATTRIBUTE_DOCSTRING = auto()  # Using PEP 257 syntax
    ENUM_ATTRIBUTE_DOCSTRING = auto()  # Using PEP 257 syntax
    DIRECTIVE_ATTRIBUTE_DOCSTRING = auto()  # Using PEP 257 syntax


class DescriptionSources:
    """
    For convenience, this class specified sets of commonly used DescriptionSources
    """

    DESCRIPTIONS = [DescriptionSource.STRAWBERRY_DESCRIPTIONS]

    DOCSTRINGS = [
        DescriptionSource.RESOLVER_DOCSTRINGS,
        DescriptionSource.DIRECTIVE_DOCSTRINGS,
        DescriptionSource.TYPE_DOCSTRINGS,
        DescriptionSource.ENUM_DOCSTRINGS,
    ]

    ATTRIBUTE_DOCSTRINGS = [
        DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING,
        DescriptionSource.ENUM_ATTRIBUTE_DOCSTRING,
        DescriptionSource.DIRECTIVE_ATTRIBUTE_DOCSTRING,
    ]

    ALL = DESCRIPTIONS + DOCSTRINGS + ATTRIBUTE_DOCSTRINGS
