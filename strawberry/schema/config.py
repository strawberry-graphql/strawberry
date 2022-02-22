from __future__ import annotations

from dataclasses import InitVar, dataclass, field

from .name_converter import EnumValueFrom, NameConverter


@dataclass
class StrawberryConfig:
    ENUM_MEMBER = EnumValueFrom.ENUM_MEMBER
    ENUM_VALUE = EnumValueFrom.ENUM_VALUE

    auto_camel_case: InitVar[bool] = None  # type: ignore
    name_converter: NameConverter = field(default_factory=NameConverter)
    enum_values_from: EnumValueFrom = ENUM_VALUE

    def __post_init__(
        self,
        auto_camel_case: bool,
    ):
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case

        self.name_converter.enum_values_from = self.enum_values_from
