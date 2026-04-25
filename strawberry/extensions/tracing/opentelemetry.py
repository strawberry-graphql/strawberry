from __future__ import annotations

import contextvars
import dataclasses
from collections.abc import Callable
from copy import deepcopy
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
)

from opentelemetry import trace
from opentelemetry.trace import SpanKind

from strawberry.extensions import LifecycleStep, SchemaExtension
from strawberry.extensions.utils import get_path_from_info

from .utils import should_skip_tracing

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from graphql import GraphQLResolveInfo
    from opentelemetry.trace import Span, Tracer

    from strawberry.types.execution import ExecutionContext


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

ArgFilter = Callable[[dict[str, Any], "GraphQLResolveInfo"], dict[str, Any]]


@dataclasses.dataclass
class _OpenTelemetryTracingState:
    """Per-request OpenTelemetry tracing state.

    Held in a context variable so a shared extension instance is safe under
    concurrent execution. Stores the active spans (operation, validation,
    parsing) and the operation name used to label them.
    """

    operation_name: str | None = None
    span_holder: dict[LifecycleStep, Span] = dataclasses.field(default_factory=dict)


_opentelemetry_state_var: contextvars.ContextVar[_OpenTelemetryTracingState | None] = (
    contextvars.ContextVar("strawberry.tracing.opentelemetry", default=None)
)


def _get_state() -> _OpenTelemetryTracingState:
    state = _opentelemetry_state_var.get()
    if state is None:
        raise RuntimeError(
            "OpenTelemetryExtension state is not initialised: this method "
            "must be called inside the on_operation lifecycle hook."
        )
    return state


class OpenTelemetryExtension(SchemaExtension):
    _arg_filter: ArgFilter | None
    _tracer: Tracer

    def __init__(
        self,
        *,
        execution_context: ExecutionContext | None = None,
        arg_filter: ArgFilter | None = None,
        tracer_provider: trace.TracerProvider | None = None,
    ) -> None:
        self._arg_filter = arg_filter
        self._tracer = trace.get_tracer("strawberry", tracer_provider=tracer_provider)

    def on_operation(self) -> Generator[None, None, None]:
        state = _OpenTelemetryTracingState()
        token = _opentelemetry_state_var.set(state)
        try:
            state.operation_name = self.execution_context.operation_name
            span_name = (
                f"GraphQL Query: {state.operation_name}"
                if state.operation_name
                else "GraphQL Query"
            )

            operation_span = self._tracer.start_span(span_name, kind=SpanKind.SERVER)
            state.span_holder[LifecycleStep.OPERATION] = operation_span
            operation_span.set_attribute("component", "graphql")

            if self.execution_context.query:
                operation_span.set_attribute("query", self.execution_context.query)

            yield

            # If the client doesn't provide an operation name then GraphQL will
            # execute the first operation in the query string. This might be a named
            # operation but we don't know until the parsing stage has finished. If
            # that's the case we want to update the span name so that we have a more
            # useful name in our trace.
            if not state.operation_name and self.execution_context.operation_name:
                span_name = f"GraphQL Query: {self.execution_context.operation_name}"
                operation_span.update_name(span_name)
        finally:
            span = state.span_holder.get(LifecycleStep.OPERATION)
            if span is not None:
                span.end()
            _opentelemetry_state_var.reset(token)

    def on_validate(self) -> Generator[None, None, None]:
        state = _get_state()
        ctx = trace.set_span_in_context(state.span_holder[LifecycleStep.OPERATION])
        validation_span = self._tracer.start_span(
            "GraphQL Validation",
            context=ctx,
        )
        state.span_holder[LifecycleStep.VALIDATION] = validation_span
        yield
        validation_span.end()

    def on_parse(self) -> Generator[None, None, None]:
        state = _get_state()
        ctx = trace.set_span_in_context(state.span_holder[LifecycleStep.OPERATION])
        parsing_span = self._tracer.start_span("GraphQL Parsing", context=ctx)
        state.span_holder[LifecycleStep.PARSE] = parsing_span

        yield
        parsing_span.end()

    def filter_resolver_args(
        self, args: dict[str, Any], info: GraphQLResolveInfo
    ) -> dict[str, Any]:
        if not self._arg_filter:
            return args
        return self._arg_filter(deepcopy(args), info)

    def convert_dict_to_allowed_types(self, value: dict) -> str:
        return (
            "{"
            + ", ".join(
                f"{k}: {self.convert_to_allowed_types(v)}" for k, v in value.items()
            )
            + "}"
        )

    def convert_to_allowed_types(self, value: Any) -> Any:
        # Put these in decreasing order of use-cases to exit as soon as possible
        if isinstance(value, (bool, str, bytes, int, float)):
            return value
        if isinstance(value, (list, tuple, range)):
            return self.convert_list_or_tuple_to_allowed_types(value)
        if isinstance(value, dict):
            return self.convert_dict_to_allowed_types(value)
        if isinstance(value, (set, frozenset)):
            return self.convert_set_to_allowed_types(value)
        if isinstance(value, complex):
            return str(value)  # Convert complex numbers to strings
        if isinstance(value, (bytearray, memoryview)):
            return bytes(value)  # Convert bytearray and memoryview to bytes
        return str(value)

    def convert_set_to_allowed_types(self, value: set | frozenset) -> str:
        return (
            "{" + ", ".join(str(self.convert_to_allowed_types(x)) for x in value) + "}"
        )

    def convert_list_or_tuple_to_allowed_types(self, value: Iterable) -> str:
        return ", ".join(map(str, map(self.convert_to_allowed_types, value)))

    def add_tags(self, span: Span, info: GraphQLResolveInfo, kwargs: Any) -> None:
        graphql_path = ".".join(map(str, get_path_from_info(info)))

        span.set_attribute("component", "graphql")
        span.set_attribute("graphql.parentType", info.parent_type.name)
        span.set_attribute("graphql.path", graphql_path)

        if kwargs:
            filtered_kwargs = self.filter_resolver_args(kwargs, info)

            for kwarg, value in filtered_kwargs.items():
                converted_value = self.convert_to_allowed_types(value)
                span.set_attribute(f"graphql.param.{kwarg}", converted_value)

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

            if isawaitable(result):  # pragma: no cover
                result = await result

            return result

        state = _get_state()
        with self._tracer.start_as_current_span(
            f"GraphQL Resolving: {info.field_name}",
            context=trace.set_span_in_context(
                state.span_holder[LifecycleStep.OPERATION]
            ),
        ) as span:
            self.add_tags(span, info, kwargs)
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result


class OpenTelemetryExtensionSync(OpenTelemetryExtension):
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
        with self._tracer.start_as_current_span(
            f"GraphQL Resolving: {info.field_name}",
            context=trace.set_span_in_context(
                state.span_holder[LifecycleStep.OPERATION]
            ),
        ) as span:
            self.add_tags(span, info, kwargs)
            return _next(root, info, *args, **kwargs)


__all__ = ["OpenTelemetryExtension", "OpenTelemetryExtensionSync"]
