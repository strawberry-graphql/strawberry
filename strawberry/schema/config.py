from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any, TypedDict

from strawberry.types.info import Info

from .name_converter import NameConverter

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from strawberry.types.scalar import ScalarDefinition


class BatchingConfig(TypedDict):
    max_operations: int


@dataclass
class StrawberryConfig:
    """Configuration for a Strawberry GraphQL schema.

    Attributes:
        auto_camel_case: Whether to automatically convert field names to camelCase.
        name_converter: The name converter to use for type/field names.
        default_resolver: The default resolver function for fields.
        relay_max_results: Maximum results for Relay connections.
        relay_use_legacy_global_id: Use legacy GlobalID format for Relay.
        disable_field_suggestions: Disable field suggestions in error messages.
        info_class: Custom Info class to use.
        enable_experimental_incremental_execution: Enable @defer/@stream support.
        scalar_map: A mapping of types to their scalar definitions. This allows
            any type (including NewType) to be used as a GraphQL scalar with
            proper type checking support.
        batching_config: Configuration for operation batching.
    """

    auto_camel_case: InitVar[bool] = None  # pyright: reportGeneralTypeIssues=false
    name_converter: NameConverter = field(default_factory=NameConverter)
    default_resolver: Callable[[Any, str], object] = getattr
    relay_max_results: int = 100
    relay_use_legacy_global_id: bool = False
    disable_field_suggestions: bool = False
    info_class: type[Info] = Info
    enable_experimental_incremental_execution: bool = False
    _unsafe_disable_same_type_validation: bool = False
    scalar_map: Mapping[object, ScalarDefinition] = field(default_factory=dict)
    batching_config: BatchingConfig | None = None

    def __post_init__(
        self,
        auto_camel_case: bool,
    ) -> None:
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case

        if not issubclass(self.info_class, Info):
            raise TypeError("`info_class` must be a subclass of strawberry.Info")


__all__ = ["StrawberryConfig"]
