from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Any, Callable, Optional

from .name_converter import NameConverter


@dataclass
class BatchingConfig:
    max_operations: int = 3


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None  # pyright: reportGeneralTypeIssues=false
    name_converter: NameConverter = field(default_factory=NameConverter)
    default_resolver: Callable[[Any, str], object] = getattr

    # Setting this means you are enabling batching
    # TODO: do I like it this?
    batching_config: Optional[BatchingConfig] = None

    def __post_init__(
        self,
        auto_camel_case: bool,
    ):
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case
