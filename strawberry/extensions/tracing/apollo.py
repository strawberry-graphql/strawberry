from __future__ import annotations

import contextvars
import dataclasses
import time
from datetime import datetime, timezone
from inspect import isawaitable
from typing import TYPE_CHECKING, Any

from strawberry.extensions import SchemaExtension
from strawberry.extensions.utils import get_path_from_info

from .utils import should_skip_tracing

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from graphql import GraphQLResolveInfo

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclasses.dataclass
class ApolloStepStats:
    start_offset: int
    duration: int

    def to_json(self) -> dict[str, Any]:
        return {"startOffset": self.start_offset, "duration": self.duration}


@dataclasses.dataclass
class ApolloResolverStats:
    path: list[str]
    parent_type: Any
    field_name: str
    return_type: Any
    start_offset: int
    duration: int | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "field_name": self.field_name,
            "parentType": str(self.parent_type),
            "returnType": str(self.return_type),
            "startOffset": self.start_offset,
            "duration": self.duration,
        }


@dataclasses.dataclass
class ApolloExecutionStats:
    resolvers: list[ApolloResolverStats]

    def to_json(self) -> dict[str, Any]:
        return {"resolvers": [resolver.to_json() for resolver in self.resolvers]}


@dataclasses.dataclass
class ApolloTracingStats:
    start_time: datetime
    end_time: datetime
    duration: int
    execution: ApolloExecutionStats
    validation: ApolloStepStats
    parsing: ApolloStepStats
    version: int = 1

    def to_json(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "startTime": self.start_time.strftime(DATETIME_FORMAT),
            "endTime": self.end_time.strftime(DATETIME_FORMAT),
            "duration": self.duration,
            "execution": self.execution.to_json(),
            "validation": self.validation.to_json(),
            "parsing": self.parsing.to_json(),
        }


@dataclasses.dataclass
class _ApolloTracingState:
    """Per-request tracing state.

    Held in a context variable so that a single ``ApolloTracingExtension``
    instance shared across concurrent requests gives each request its own
    timing buffer and resolver stats.
    """

    resolver_stats: list[ApolloResolverStats]
    start_timestamp: int
    end_timestamp: int
    start_time: datetime
    end_time: datetime
    start_parsing: int
    end_parsing: int
    start_validation: int
    end_validation: int


_apollo_state_var: contextvars.ContextVar[_ApolloTracingState | None] = (
    contextvars.ContextVar("strawberry.tracing.apollo", default=None)
)


def _get_state() -> _ApolloTracingState:
    state = _apollo_state_var.get()
    if state is None:
        raise RuntimeError(
            "ApolloTracingExtension state is not initialised: this method "
            "must be called inside the on_operation lifecycle hook."
        )
    return state


class ApolloTracingExtension(SchemaExtension):
    def now(self) -> int:
        return time.perf_counter_ns()

    def on_operation(self) -> Generator[None, None, None]:
        now = self.now()
        start_time = datetime.now(timezone.utc)
        state = _ApolloTracingState(
            resolver_stats=[],
            start_timestamp=now,
            end_timestamp=now,
            start_time=start_time,
            end_time=start_time,
            start_parsing=now,
            end_parsing=now,
            start_validation=now,
            end_validation=now,
        )
        token = _apollo_state_var.set(state)
        try:
            yield
        finally:
            state.end_timestamp = self.now()
            state.end_time = datetime.now(timezone.utc)
            # Publish the per-request tracing payload onto the
            # ``ExecutionContext`` before clearing state, so the extensions
            # runner can pick it up after this hook exits without needing
            # to read the ContextVar again.
            stats = self.stats
            assert stats is not None
            self.execution_context.extensions_results["tracing"] = stats.to_json()
            _apollo_state_var.reset(token)

    def on_parse(self) -> Generator[None, None, None]:
        state = _get_state()
        state.start_parsing = self.now()
        try:
            yield
        finally:
            state.end_parsing = self.now()

    def on_validate(self) -> Generator[None, None, None]:
        state = _get_state()
        state.start_validation = self.now()
        try:
            yield
        finally:
            state.end_validation = self.now()

    @property
    def stats(self) -> ApolloTracingStats | None:
        """Snapshot of the current request's tracing stats.

        Returns ``None`` when accessed outside an active ``on_operation``
        — i.e. once the per-request state ContextVar has been reset.
        """
        state = _apollo_state_var.get()
        if state is None:
            return None
        return ApolloTracingStats(
            start_time=state.start_time,
            end_time=state.end_time,
            duration=state.end_timestamp - state.start_timestamp,
            execution=ApolloExecutionStats(state.resolver_stats),
            validation=ApolloStepStats(
                start_offset=state.start_validation - state.start_timestamp,
                duration=state.end_validation - state.start_validation,
            ),
            parsing=ApolloStepStats(
                start_offset=state.start_parsing - state.start_timestamp,
                duration=state.end_parsing - state.start_parsing,
            ),
        )

    def get_results(self) -> dict[str, dict[str, Any]]:
        """Return the tracing payload for the current request.

        Called by ``SchemaExtensionsRunner`` either *during* the operation
        (e.g. on an early-return triggered by a parse error) or *after*
        it. While the operation is still active the state is in the
        ContextVar, so the payload is built from there. Once
        ``on_operation``'s ``finally`` has reset the token, the payload
        has already been published onto
        ``execution_context.extensions_results`` and returning ``{}``
        lets the runner pick that up.
        """
        stats = self.stats
        if stats is None:
            return {}
        return {"tracing": stats.to_json()}

    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> Any:
        if should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result  # pragma: no cover

            return result

        state = _get_state()
        start_timestamp = self.now()

        resolver_stats = ApolloResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - state.start_timestamp,
        )

        try:
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result
        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            state.resolver_stats.append(resolver_stats)


class ApolloTracingExtensionSync(ApolloTracingExtension):
    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> Any:
        if should_skip_tracing(_next, info):
            return _next(root, info, *args, **kwargs)

        state = _get_state()
        start_timestamp = self.now()

        resolver_stats = ApolloResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - state.start_timestamp,
        )

        try:
            return _next(root, info, *args, **kwargs)
        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            state.resolver_stats.append(resolver_stats)


__all__ = ["ApolloTracingExtension", "ApolloTracingExtensionSync"]
