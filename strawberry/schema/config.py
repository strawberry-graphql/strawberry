import enum
from dataclasses import dataclass


@dataclass
class StrawberryConfig:
    class EnumNameExport(enum.Enum):
        VALUE = enum.auto()
        NAME = enum.auto()

    auto_camel_case: bool = True
    enum_values: EnumNameExport = EnumNameExport.NAME
