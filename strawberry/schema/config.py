from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Any, Callable, Optional, TypedDict

from strawberry.types.info import Info

from .name_converter import NameConverter


class BatchingConfig(TypedDict):
    max_operations: int


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None  # pyright: reportGeneralTypeIssues=false
    name_converter: NameConverter = field(default_factory=NameConverter)
    default_resolver: Callable[[Any, str], object] = getattr
    relay_max_results: int = 100
    relay_use_legacy_global_id: bool = False
    disable_field_suggestions: bool = False
    info_class: type[Info] = Info
    enable_experimental_incremental_execution: bool = False
    _unsafe_disable_same_type_validation: bool = False
    batching_config: Optional[BatchingConfig] = None

    def __post_init__(
        self,
        auto_camel_case: bool,
    ) -> None:
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case

        if not issubclass(self.info_class, Info):
            raise TypeError("`info_class` must be a subclass of strawberry.Info")


__all__ = ["StrawberryConfig"]
