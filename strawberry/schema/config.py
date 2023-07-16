from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Any, Callable, Optional
from typing_extensions import Required, TypedDict

from .name_converter import NameConverter


class BatchingConfig(TypedDict, total=False):
    enabled: Required[bool]
    max_operations: int


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None  # pyright: ignore[reportGeneralTypeIssues]
    name_converter: NameConverter = field(default_factory=NameConverter)
    default_resolver: Callable[[Any, str], object] = getattr
    relay_max_results: int = 100

    batching_config: BatchingConfig = None  # type: ignore

    def __post_init__(
        self,
        auto_camel_case: Optional[bool],
    ):
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case

        if self.batching_config is None:  # type: ignore
            self.batching_config = {"enabled": False}
