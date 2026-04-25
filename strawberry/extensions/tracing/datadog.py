from __future__ import annotations

import contextvars
import dataclasses
import hashlib
from inspect import isawaitable
from typing import TYPE_CHECKING, Any

import ddtrace
from packaging import version

from strawberry.extensions import LifecycleStep, SchemaExtension
from strawberry.extensions.tracing.utils import should_skip_tracing

parsed_ddtrace_version = version.parse(ddtrace.__version__)
if parsed_ddtrace_version >= version.parse("3.0.0"):
    from ddtrace.trace import Span, tracer
else:
    from ddtrace import Span, tracer


if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterator

    from graphql import GraphQLResolveInfo


@dataclasses.dataclass
class _DatadogTracingState:
    """Per-request Datadog tracing state.

    Held in a context variable so a shared extension instance is safe under
    concurrent execution.
    """

    operation_name: str | None = None
    resource_name: str | None = None
    request_span: Span | None = None
    validation_span: Span | None = None
    parsing_span: Span | None = None


_datadog_state_var: contextvars.ContextVar[_DatadogTracingState | None] = (
    contextvars.ContextVar("strawberry.tracing.datadog", default=None)
)


def _get_state() -> _DatadogTracingState:
    state = _datadog_state_var.get()
    if state is None:
        raise RuntimeError(
            "DatadogTracingExtension state is not initialised: this method "
            "must be called inside the on_operation lifecycle hook."
        )
    return state


class DatadogTracingExtension(SchemaExtension):
    @property
    def _resource_name(self) -> str:
        """Datadog resource name for the current request, computed lazily.

        Cached on the per-request state so multiple accesses don't re-hash.
        Override this in a subclass to customise the resource label.
        """
        state = _get_state()
        if state.resource_name is not None:
            return state.resource_name

        if self.execution_context.query is None:
            state.resource_name = "query_missing"
            return state.resource_name

        query_hash = self.hash_query(self.execution_context.query)

        if self.execution_context.operation_name:
            state.resource_name = (
                f"{self.execution_context.operation_name}:{query_hash}"
            )
        else:
            state.resource_name = query_hash
        return state.resource_name

    def create_span(
        self,
        lifecycle_step: LifecycleStep,
        name: str,
        **kwargs: Any,
    ) -> Span:
        """Create a span with the given name and kwargs.

        You can  override this if you want to add more tags to the span.

        Example:

        ```python
        class CustomExtension(DatadogTracingExtension):
            def create_span(self, lifecycle_step, name, **kwargs):
                span = super().create_span(lifecycle_step, name, **kwargs)
                if lifecycle_step == LifeCycleStep.OPERATION:
                    span.set_tag("graphql.query", self.execution_context.query)
                return span
        ```
        """
        return tracer.trace(
            name,
            span_type="graphql",
            **kwargs,
        )

    def hash_query(self, query: str) -> str:
        return hashlib.md5(query.encode("utf-8")).hexdigest()  # noqa: S324

    def on_operation(self) -> Iterator[None]:
        state = _DatadogTracingState()
        token = _datadog_state_var.set(state)
        try:
            state.operation_name = self.execution_context.operation_name
            span_name = (
                f"{state.operation_name}" if state.operation_name else "Anonymous Query"
            )

            request_span = self.create_span(
                LifecycleStep.OPERATION,
                span_name,
                resource=self._resource_name,
                service="strawberry",
            )
            state.request_span = request_span
            request_span.set_tag("graphql.operation_name", state.operation_name)

            query = self.execution_context.query

            if query is not None:
                query = query.strip()
                operation_type = "query"

                if query.startswith("mutation"):
                    operation_type = "mutation"
                elif query.startswith("subscription"):  # pragma: no cover
                    operation_type = "subscription"
            else:
                operation_type = "query_missing"

            request_span.set_tag("graphql.operation_type", operation_type)

            yield
        finally:
            if state.request_span is not None:
                state.request_span.finish()
            _datadog_state_var.reset(token)

    def on_validate(self) -> Generator[None, None, None]:
        state = _get_state()
        validation_span = self.create_span(
            lifecycle_step=LifecycleStep.VALIDATION,
            name="Validation",
        )
        state.validation_span = validation_span
        yield
        validation_span.finish()

    def on_parse(self) -> Generator[None, None, None]:
        state = _get_state()
        parsing_span = self.create_span(
            lifecycle_step=LifecycleStep.PARSE,
            name="Parsing",
        )
        state.parsing_span = parsing_span
        yield
        parsing_span.finish()

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

        field_path = f"{info.parent_type}.{info.field_name}"

        with self.create_span(
            lifecycle_step=LifecycleStep.RESOLVE,
            name=f"Resolving: {field_path}",
        ) as span:
            span.set_tag("graphql.field_name", info.field_name)
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_path", field_path)
            span.set_tag("graphql.path", ".".join(map(str, info.path.as_list())))

            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result


class DatadogTracingExtensionSync(DatadogTracingExtension):
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

        field_path = f"{info.parent_type}.{info.field_name}"

        with self.create_span(
            lifecycle_step=LifecycleStep.RESOLVE,
            name=f"Resolving: {field_path}",
        ) as span:
            span.set_tag("graphql.field_name", info.field_name)
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_path", field_path)
            span.set_tag("graphql.path", ".".join(map(str, info.path.as_list())))

            return _next(root, info, *args, **kwargs)


__all__ = ["DatadogTracingExtension", "DatadogTracingExtensionSync"]
