from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Any, Callable, TypedDict
from typing_extensions import Required

from strawberry.types.info import Info

from .name_converter import NameConverter


class BatchingConfig(TypedDict, total=False):
    enabled: Required[bool]
    max_operations: int
    share_context: Required[bool]


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None  # pyright: reportGeneralTypeIssues=false
    name_converter: NameConverter = field(default_factory=NameConverter)
    default_resolver: Callable[[Any, str], object] = getattr
    relay_max_results: int = 100
    disable_field_suggestions: bool = False
    info_class: type[Info] = Info

    batching_config: BatchingConfig = None  # type: ignore

    def __post_init__(
        self,
        auto_camel_case: bool,
    ) -> None:
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case

        if not issubclass(self.info_class, Info):
            raise TypeError("`info_class` must be a subclass of strawberry.Info")
        if self.batching_config is None:  # type: ignore
            self.batching_config = {"enabled": False, "share_context": True}

        if self.batching_config.get("enabled") and not self.batching_config.get(
            "share_context"
        ):
            raise ValueError("Disabling context sharing is not supported currently.")


__all__ = ["StrawberryConfig"]
