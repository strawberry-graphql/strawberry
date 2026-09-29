from __future__ import annotations

# Imported at runtime (not under TYPE_CHECKING) on purpose: StrawberryConfigDict
# is a public TypedDict, and tools like typing.get_type_hints() can only
# resolve its field types when the names are available at runtime.
from collections.abc import Callable, Mapping  # noqa: TC003
from dataclasses import InitVar, dataclass, field
from typing import Any, TypedDict

from strawberry.types.info import Info
from strawberry.types.scalar import ScalarDefinition  # noqa: TC001

from .name_converter import NameConverter


class BatchingConfig(TypedDict):
    max_operations: int


class StrawberryConfigDict(TypedDict, total=False):
    """Dictionary-based configuration for a Strawberry GraphQL schema.

    This is the preferred way to configure a schema:

    ```python
    schema = strawberry.Schema(query=Query, config={"auto_camel_case": False})
    ```

    All keys are optional; any key that is omitted falls back to the default
    value of `StrawberryConfig`.
    """

    auto_camel_case: bool
    name_converter: NameConverter
    default_resolver: Callable[[Any, str], object]
    relay_max_results: int
    relay_use_legacy_global_id: bool
    disable_field_suggestions: bool
    info_class: type[Info]
    enable_experimental_incremental_execution: bool
    _unsafe_disable_same_type_validation: bool
    scalar_map: Mapping[object, ScalarDefinition]
    batching_config: BatchingConfig | None


def normalize_config(
    config: StrawberryConfig | StrawberryConfigDict | None,
) -> StrawberryConfig:
    """Normalize the `config` argument of `Schema` to a `StrawberryConfig`.

    Accepts `None` (use defaults), a `StrawberryConfig` instance (used as is),
    or a plain dictionary matching `StrawberryConfigDict` (converted to a
    `StrawberryConfig`, so the rest of the codebase keeps working with
    attribute access).
    """
    if config is None:
        return StrawberryConfig()
    if isinstance(config, dict):
        return StrawberryConfig(**config)
    return config


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


__all__ = ["StrawberryConfig", "StrawberryConfigDict", "normalize_config"]
