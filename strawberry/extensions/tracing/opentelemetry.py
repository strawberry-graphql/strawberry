import enum
from copy import deepcopy
from inspect import isawaitable
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Tracer

from graphql import GraphQLResolveInfo

from strawberry.extensions import Extension
from strawberry.extensions.utils import get_path_from_info
from strawberry.types.execution import ExecutionContext

from .utils import should_skip_tracing


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

ArgFilter = Callable[[Dict[str, Any], GraphQLResolveInfo], Dict[str, Any]]


class RequestStage(enum.Enum):
    REQUEST = enum.auto()
    PARSING = enum.auto()
    VALIDATION = enum.auto()


class OpenTelemetryExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _span_holder: Dict[str, Span] = dict()
    _tracer: Tracer

    def __init__(
        self,
        *,
        execution_context: Optional[ExecutionContext] = None,
        arg_filter: Optional[ArgFilter] = None,
    ):
        self._arg_filter = arg_filter
        self._tracer = trace.get_tracer("strawberry")
        if execution_context:
            self.execution_context = execution_context

    def on_request_start(self):
        span_name = (
            f"GraphQL Query: {self.execution_context.operation_name}"
            if self.execution_context.operation_name
            else "GraphQL Query"
        )

        self._span_holder[RequestStage.REQUEST] = self._tracer.start_span(
            span_name, kind=SpanKind.SERVER
        )
        self._span_holder[RequestStage.REQUEST].set_attribute("component", "graphql")
        self._span_holder[RequestStage.REQUEST].set_attribute(
            "query", self.execution_context.query
        )

    def on_request_end(self):
        self._span_holder[RequestStage.REQUEST].end()

    def on_validation_start(self):
        ctx = trace.set_span_in_context(self._span_holder[RequestStage.REQUEST])
        self._span_holder[RequestStage.VALIDATION] = self._tracer.start_span(
            "GraphQL Validation",
            context=ctx,
        )

    def on_validation_end(self):
        self._span_holder[RequestStage.VALIDATION].end()

    def on_parsing_start(self):
        ctx = trace.set_span_in_context(self._span_holder[RequestStage.REQUEST])
        self._span_holder[RequestStage.PARSING] = self._tracer.start_span(
            "GraphQL Parsing", context=ctx
        )

    def on_parsing_end(self):
        self._span_holder[RequestStage.PARSING].end()

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

        with self._tracer.start_as_current_span(
            f"GraphQL Resolving: {info.field_name}",
            context=trace.set_span_in_context(self._span_holder[RequestStage.REQUEST]),
        ) as span:
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

        with self._tracer.start_as_current_span(
            "GraphQL Resolving: {info.field_name}",
            context=trace.set_span_in_context(self._span_holder[RequestStage.REQUEST]),
        ) as span:
            self.add_tags(span, info, kwargs)
            result = _next(root, info, *args, **kwargs)

            return result
