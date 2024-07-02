from __future__ import annotations

import hashlib
import warnings
from functools import cached_property
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, Callable, Generator, Optional

from sentry_sdk import configure_scope, start_span

from strawberry.extensions import SchemaExtension
from strawberry.extensions.tracing.utils import should_skip_tracing

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.types.execution import ExecutionContext


class SentryTracingExtension(SchemaExtension):
    def __init__(
        self,
        *,
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        warnings.warn(
            "The Sentry tracing extension is deprecated, please update to sentry>=1.32.0",
            DeprecationWarning,
            stacklevel=2,
        )

        if execution_context:
            self.execution_context = execution_context

    @cached_property
    def _resource_name(self) -> str:
        assert self.execution_context.query

        query_hash = self.hash_query(self.execution_context.query)

        if self.execution_context.operation_name:
            return f"{self.execution_context.operation_name}:{query_hash}"

        return query_hash

    def hash_query(self, query: str) -> str:
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def on_operation(self) -> Generator[None, None, None]:
        self._operation_name = self.execution_context.operation_name
        name = f"{self._operation_name}" if self._operation_name else "Anonymous Query"

        with configure_scope() as scope:
            if scope.span:
                self.gql_span = scope.span.start_child(
                    op="gql",
                    description=name,
                )
            else:
                self.gql_span = start_span(
                    op="gql",
                )

        operation_type = "query"

        assert self.execution_context.query

        if self.execution_context.query.strip().startswith("mutation"):
            operation_type = "mutation"
        if self.execution_context.query.strip().startswith("subscription"):
            operation_type = "subscription"

        self.gql_span.set_tag("graphql.operation_type", operation_type)
        self.gql_span.set_tag("graphql.resource_name", self._resource_name)
        self.gql_span.set_data("graphql.query", self.execution_context.query)

        yield

        self.gql_span.finish()

    def on_validate(self) -> Generator[None, None, None]:
        self.validation_span = self.gql_span.start_child(
            op="validation", description="Validation"
        )

        yield

        self.validation_span.finish()

    def on_parse(self) -> Generator[None, None, None]:
        self.parsing_span = self.gql_span.start_child(
            op="parsing", description="Parsing"
        )

        yield

        self.parsing_span.finish()

    def should_skip_tracing(self, _next: Callable, info: GraphQLResolveInfo) -> bool:
        return should_skip_tracing(_next, info)

    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> Any:
        if self.should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):  # pragma: no cover
                result = await result

            return result

        field_path = f"{info.parent_type}.{info.field_name}"

        with self.gql_span.start_child(
            op="resolve", description=f"Resolving: {field_path}"
        ) as span:
            span.set_tag("graphql.field_name", info.field_name)
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_path", field_path)
            span.set_tag("graphql.path", ".".join(map(str, info.path.as_list())))

            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result


class SentryTracingExtensionSync(SentryTracingExtension):
    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> Any:
        if self.should_skip_tracing(_next, info):
            return _next(root, info, *args, **kwargs)

        field_path = f"{info.parent_type}.{info.field_name}"

        with self.gql_span.start_child(
            op="resolve", description=f"Resolving: {field_path}"
        ) as span:
            span.set_tag("graphql.field_name", info.field_name)
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_path", field_path)
            span.set_tag("graphql.path", ".".join(map(str, info.path.as_list())))

            return _next(root, info, *args, **kwargs)
