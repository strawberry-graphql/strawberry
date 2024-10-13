from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Any, Callable

from strawberry.types.info import Info

from .name_converter import NameConverter


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None  # pyright: reportGeneralTypeIssues=false
    name_converter: NameConverter = field(default_factory=NameConverter)
    default_resolver: Callable[[Any, str], object] = getattr
    relay_max_results: int = 100
    disable_field_suggestions: bool = False
    info_class: type[Info] = Info

    def __post_init__(
        self,
        auto_camel_case: bool,
    ) -> None:
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case

        if not issubclass(self.info_class, Info):
            raise TypeError("`info_class` must be a subclass of strawberry.Info")


__all__ = ["StrawberryConfig"]
