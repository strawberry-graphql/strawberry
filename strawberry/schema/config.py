from __future__ import annotations

from dataclasses import InitVar, dataclass, field

from .name_converter import NameConverter


@dataclass
class StrawberryConfig:
    name_converter: NameConverter

    def __init__(
        self,
        auto_camel_case: bool = True,
        name_converter: NameConverter = None,
    ):
        self.name_converter = name_converter or NameConverter(auto_camel_case)
