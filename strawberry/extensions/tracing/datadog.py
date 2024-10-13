from __future__ import annotations

import hashlib
from functools import lru_cache
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, Callable, Generator, Iterator

from ddtrace import Span, tracer

from strawberry.extensions import LifecycleStep, SchemaExtension
from strawberry.extensions.tracing.utils import should_skip_tracing

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.types.execution import ExecutionContext


class DatadogTracingExtension(SchemaExtension):
    @lru_cache
    def _resource_name(self, execution_context: ExecutionContext) -> str:
        if execution_context.query is None:
            return "query_missing"

        query_hash = self.hash_query(execution_context.query)

        if execution_context.operation_name:
            return f"{execution_context.operation_name}:{query_hash}"

        return query_hash

    @classmethod
    def create_span(
        cls,
        lifecycle_step: LifecycleStep,
        execution_context: ExecutionContext,
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
                    span.set_tag("graphql.query", execution_context.query)
                return span
        ```
        """
        return tracer.trace(
            name,
            span_type="graphql",
            **kwargs,
        )

    def hash_query(self, query: str) -> str:
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def on_operation(self, execution_context: ExecutionContext) -> Iterator[None]:
        self._operation_name = execution_context.operation_name
        span_name = (
            f"{self._operation_name}" if self._operation_name else "Anonymous Query"
        )

        request_span = self.create_span(
            LifecycleStep.OPERATION,
            execution_context,
            span_name,
            resource=self._resource_name(execution_context),
            service="strawberry",
        )
        request_span.set_tag("graphql.operation_name", self._operation_name)

        query = execution_context.query

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

        request_span.finish()

    def on_validate(
        self, execution_context: ExecutionContext
    ) -> Generator[None, None, None]:
        validation_span = self.create_span(
            lifecycle_step=LifecycleStep.VALIDATION,
            execution_context=execution_context,
            name="Validation",
        )
        yield
        validation_span.finish()

    def on_parse(
        self, execution_context: ExecutionContext
    ) -> Generator[None, None, None]:
        self.parsing_span = self.create_span(
            lifecycle_step=LifecycleStep.PARSE,
            execution_context=execution_context,
            name="Parsing",
        )
        yield
        self.parsing_span.finish()

    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        execution_context: ExecutionContext,
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
            execution_context=execution_context,
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
