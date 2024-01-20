from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Any, Callable, TypedDict

from .name_converter import NameConverter


class StrawberryConfigDict(TypedDict, total=False):
    auto_camel_case: bool
    name_converter: NameConverter
    default_resolver: Callable[[Any, str], object]
    relay_max_results: int


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None  # pyright: reportGeneralTypeIssues=false
    name_converter: NameConverter = field(default_factory=NameConverter)
    default_resolver: Callable[[Any, str], object] = getattr
    relay_max_results: int = 100

    def __post_init__(
        self,
        auto_camel_case: bool,
    ):
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case

    @classmethod
    def from_dict(cls, data: StrawberryConfigDict | None) -> StrawberryConfig:
        if not data:
            return cls()
        return cls(**data)
