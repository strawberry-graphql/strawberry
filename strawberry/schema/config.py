from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from strawberry.types.info import Info

from .name_converter import NameConverter

if TYPE_CHECKING:
    from collections.abc import Callable


class BatchingConfig(TypedDict):
    max_operations: int


class StrawberryConfigType(TypedDict, total=False):
    """Type definition for Strawberry configuration.

    This TypedDict defines the shape of configuration options. All fields are optional.
    """

    auto_camel_case: bool | None
    name_converter: NameConverter
    default_resolver: Callable[[Any, str], object]
    relay_max_results: int
    relay_use_legacy_global_id: bool
    disable_field_suggestions: bool
    info_class: type[Info]
    enable_experimental_incremental_execution: bool
    _unsafe_disable_same_type_validation: bool
    batching_config: BatchingConfig | None


class StrawberryConfigDict(dict[str, Any]):
    """Configuration for Strawberry Schema.

    This is a dictionary-like class that defines the configuration options for a
    Strawberry schema. All fields are optional - missing fields will be filled with
    sensible defaults.

    This class supports both dictionary-style access (config["name_converter"]) and
    attribute-style access (config.name_converter) for backwards compatibility.

    Example:
        ```python
        schema = strawberry.Schema(
            query=Query,
            config={
                "auto_camel_case": True,
                "relay_max_results": 50,
            },
        )
        ```

    Attributes:
        auto_camel_case: If True, field names will be converted to camelCase.
            This is a shorthand for setting name_converter.auto_camel_case.
        name_converter: Custom name converter for field/type name transformations.
        default_resolver: Function used to resolve field values (default: getattr).
        relay_max_results: Maximum number of results for relay connections (default: 100).
        relay_use_legacy_global_id: Use legacy global ID format (default: False).
        disable_field_suggestions: Disable field name suggestions in errors (default: False).
        info_class: Custom Info class to use (default: strawberry.Info).
        enable_experimental_incremental_execution: Enable @defer/@stream support (default: False).
        _unsafe_disable_same_type_validation: Skip duplicate type validation (default: False).
        batching_config: Configuration for query batching (default: None).
    """

    if TYPE_CHECKING:
        # For type checkers, show these as instance attributes
        auto_camel_case: bool | None
        name_converter: NameConverter
        default_resolver: Callable[[Any, str], object]
        relay_max_results: int
        relay_use_legacy_global_id: bool
        disable_field_suggestions: bool
        info_class: type[Info]
        enable_experimental_incremental_execution: bool
        _unsafe_disable_same_type_validation: bool
        batching_config: BatchingConfig | None

    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access for backwards compatibility."""
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from None

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow attribute-style setting for backwards compatibility."""
        self[name] = value

    def __delattr__(self, name: str) -> None:
        """Allow attribute-style deletion for backwards compatibility."""
        try:
            del self[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from None


def _complete_config(
    config: StrawberryConfigType | StrawberryConfigDict | dict[str, Any] | None,
) -> StrawberryConfigDict:
    """Normalize and complete a config dict with defaults.

    This function takes a partial or complete config dict and ensures all required
    fields are present with appropriate defaults.

    Args:
        config: Partial config dict or None

    Returns:
        Complete StrawberryConfigDict with all defaults applied

    Raises:
        TypeError: If info_class is not a subclass of strawberry.Info
    """
    if config is None:
        config = {}

    # Create a StrawberryConfigDict (or copy if already one)
    result = StrawberryConfigDict(config)

    # Handle auto_camel_case -> name_converter conversion
    auto_camel_case = result.pop("auto_camel_case", None)

    # Apply defaults
    if "name_converter" not in result:
        result["name_converter"] = NameConverter()

    if auto_camel_case is not None:
        result["name_converter"].auto_camel_case = auto_camel_case

    # Validate info_class if provided
    info_class = result.get("info_class", Info)
    if not issubclass(info_class, Info):
        raise TypeError("`info_class` must be a subclass of strawberry.Info")

    # Set other defaults
    result.setdefault("default_resolver", getattr)
    result.setdefault("relay_max_results", 100)
    result.setdefault("relay_use_legacy_global_id", False)
    result.setdefault("disable_field_suggestions", False)
    result.setdefault("info_class", info_class)
    result.setdefault("enable_experimental_incremental_execution", False)
    result.setdefault("_unsafe_disable_same_type_validation", False)
    result.setdefault("batching_config", None)

    return result


# Backwards compatibility: StrawberryConfig is StrawberryConfigDict
# This works at runtime and for type checking because StrawberryConfigDict
# has TYPE_CHECKING annotations that make attributes visible to type checkers
StrawberryConfig = StrawberryConfigDict


__all__ = [
    "StrawberryConfig",
    "StrawberryConfigDict",
    "StrawberryConfigType",
    "_complete_config",
]
