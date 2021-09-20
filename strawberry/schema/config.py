from dataclasses import dataclass

from typing_extensions import Final


@dataclass
class StrawberryConfig:
    ENUM_VALUE: Final[str] = "ENUM_VALUE"
    ENUM_NAME: Final[str] = "ENUM_NAME"

    auto_camel_case: bool = True
    enum_values: str = ENUM_NAME
