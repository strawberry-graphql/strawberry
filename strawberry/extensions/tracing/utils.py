from __future__ import annotations

from typing import TYPE_CHECKING, Any

from strawberry.extensions.utils import is_introspection_field
from strawberry.resolvers import is_default_resolver

if TYPE_CHECKING:
    from collections.abc import Callable

    from strawberry.types.info import Info


def should_skip_tracing(resolver: Callable[..., Any], info: Info) -> bool:
    raw_info = info._raw_info
    if info.field_name not in raw_info.parent_type.fields:
        return True
    resolver = raw_info.parent_type.fields[info.field_name].resolve
    return (
        is_introspection_field(info)
        or is_default_resolver(resolver)
        or resolver is None
    )


__all__ = ["should_skip_tracing"]
