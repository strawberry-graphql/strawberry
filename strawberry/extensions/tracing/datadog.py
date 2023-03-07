from __future__ import annotations

import hashlib
from inspect import isawaitable
from typing import TYPE_CHECKING, Iterator, Optional

from ddtrace import tracer

from strawberry.extensions import SchemaExtension
from strawberry.extensions.tracing.utils import should_skip_tracing
from strawberry.utils.cached_property import cached_property

if TYPE_CHECKING:
    from strawberry.types.execution import ExecutionContext


class DatadogTracingExtension(SchemaExtension):
    def __init__(
        self,
        *,
        execution_context: Optional[ExecutionContext] = None,
    ):
        if execution_context:
            self.execution_context = execution_context

    @cached_property
    def _resource_name(self):
        assert self.execution_context.query

        query_hash = self.hash_query(self.execution_context.query)

        if self.execution_context.operation_name:
            return f"{self.execution_context.operation_name}:{query_hash}"

        return query_hash

    def hash_query(self, query: str):
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def on_operation(self) -> Iterator[None]:
        self._operation_name = self.execution_context.operation_name
        span_name = (
            f"{self._operation_name}" if self._operation_name else "Anonymous Query"
        )

        self.request_span = tracer.trace(
            span_name,
            resource=self._resource_name,
            span_type="graphql",
            service="strawberry",
        )
        self.request_span.set_tag("graphql.operation_name", self._operation_name)

        operation_type = "query"

        assert self.execution_context.query

        if self.execution_context.query.strip().startswith("mutation"):
            operation_type = "mutation"
        if self.execution_context.query.strip().startswith("subscription"):
            operation_type = "subscription"

        self.request_span.set_tag("graphql.operation_type", operation_type)
        yield
        self.request_span.finish()

    def on_validate(self):
        self.validation_span = tracer.trace("Validation", span_type="graphql")
        yield
        self.validation_span.finish()

    def on_parse(self):
        self.parsing_span = tracer.trace("Parsing", span_type="graphql")
        yield
        self.parsing_span.finish()

    async def resolve(self, _next, root, info, *args, **kwargs):
        if should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):  # pragma: no cover
                result = await result

            return result

        field_path = f"{info.parent_type}.{info.field_name}"

        with tracer.trace(f"Resolving: {field_path}", span_type="graphql") as span:
            span.set_tag("graphql.field_name", info.field_name)
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_path", field_path)
            span.set_tag("graphql.path", ".".join(map(str, info.path.as_list())))

            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result


class DatadogTracingExtensionSync(DatadogTracingExtension):
    def resolve(self, _next, root, info, *args, **kwargs):
        if should_skip_tracing(_next, info):
            return _next(root, info, *args, **kwargs)

        field_path = f"{info.parent_type}.{info.field_name}"

        with tracer.trace(f"Resolving: {field_path}", span_type="graphql") as span:
            span.set_tag("graphql.field_name", info.field_name)
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_path", field_path)
            span.set_tag("graphql.path", ".".join(map(str, info.path.as_list())))

            return _next(root, info, *args, **kwargs)
