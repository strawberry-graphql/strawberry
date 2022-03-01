from enum import Enum, auto


class DescriptionSource(Enum):
    STRAWBERRY_DESCRIPTIONS = auto()  # e.g., strawberry.type(description="...")
    RESOLVER_DOCSTRINGS = auto()
    # TODO: ATTRIBUTE_DOCSTRING = auto()  # Using PEP 257 syntax
    TYPE_DOCSTRINGS = auto()
    ENUM_DOCSTRINGS = auto()
    DIRECTIVE_DOCSTRINGS = auto()
