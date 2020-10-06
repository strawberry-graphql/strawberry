from copy import deepcopy
from inspect import isawaitable
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Tracer

from graphql import GraphQLResolveInfo

from strawberry.extensions import Extension
from strawberry.types.execution import ExecutionContext

from .utils import get_path_from_info, should_skip_tracing


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

ArgFilter = Callable[[Dict[str, Any], GraphQLResolveInfo], Dict[str, Any]]


class OpenTelemetryExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _root_span: Span
    _tracer: Tracer

    def __init__(self, *, arg_filter: Optional[ArgFilter] = None):
        self._arg_filter = arg_filter
        self._tracer = trace.get_tracer("strawberry")

    def on_request_start(self, *, execution_context: ExecutionContext):
        span_name = (
            f"GraphQL Query: {execution_context.operation_name}"
            if execution_context.operation_name
            else "GraphQL Query"
        )

        self._root_span = self._tracer.start_span(span_name, kind=SpanKind.SERVER)
        self._root_span.set_attribute("component", "graphql")
        self._root_span.set_attribute("query", execution_context.query)

    def on_request_end(self, *, execution_context: ExecutionContext):
        self._root_span.end()

    def filter_resolver_args(
        self, args: Dict[str, Any], info: GraphQLResolveInfo
    ) -> Dict[str, Any]:
        if not self._arg_filter:
            return args
        return self._arg_filter(deepcopy(args), info)

    def add_tags(self, span: Span, info: GraphQLResolveInfo, kwargs: Dict[str, Any]):
        graphql_path = ".".join(map(str, get_path_from_info(info)))

        span.set_attribute("component", "graphql")
        span.set_attribute("graphql.parentType", info.parent_type.name)
        span.set_attribute("graphql.path", graphql_path)

        if kwargs:
            filtered_kwargs = self.filter_resolver_args(kwargs, info)

            for kwarg, value in filtered_kwargs.items():
                span.set_attribute(f"graphql.param.{kwarg}", value)

    async def resolve(self, _next, root, info, *args, **kwargs):
        if should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):  # pragma: no cover
                result = await result

            return result

        with self._tracer.use_span(self._root_span):
            with self._tracer.start_span(info.field_name, kind=SpanKind.SERVER) as span:
                self.add_tags(span, info, kwargs)
                result = _next(root, info, *args, **kwargs)

                if isawaitable(result):
                    result = await result

                return result


class OpenTelemetryExtensionSync(OpenTelemetryExtension):
    def resolve(self, _next, root, info, *args, **kwargs):
        if should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            return result

        with self._tracer.use_span(self._root_span):
            with self._tracer.start_span(info.field_name, kind=SpanKind.SERVER) as span:
                self.add_tags(span, info, kwargs)
                result = _next(root, info, *args, **kwargs)

                return result
