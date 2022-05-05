from __future__ import annotations

from dataclasses import InitVar, dataclass, field

from .name_converter import NameConverter


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None
    name_converter: NameConverter = field(default_factory=NameConverter)

    def __post_init__(
        self,
        auto_camel_case: bool,
    ):
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case
