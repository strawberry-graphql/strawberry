from enum import Enum, auto


class DescriptionSource(Enum):
    STRAWBERRY_DESCRIPTIONS = auto()  # e.g., strawberry.type(description="...")
    RESOLVER_DOCSTRINGS = auto()
    DIRECTIVE_DOCSTRINGS = auto()
    TYPE_DOCSTRINGS = auto()
    TYPE_ATTRIBUTE_DOCSTRING = auto()  # Using PEP 257 syntax
    ENUM_DOCSTRINGS = auto()
    ENUM_ATTRIBUTE_DOCSTRING = auto()  # Using PEP 257 syntax
