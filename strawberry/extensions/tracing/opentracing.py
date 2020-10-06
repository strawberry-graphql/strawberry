from copy import deepcopy
from inspect import isawaitable
from typing import Any, Callable, Dict, Optional

from graphql import GraphQLResolveInfo
from opentracing import Scope, Tracer, global_tracer
from opentracing.ext import tags
from strawberry.extensions import Extension
from strawberry.types.execution import ExecutionContext
from strawberry.utils.info import get_path_from_info

from .utils import should_trace


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

ArgFilter = Callable[[Dict[str, Any], GraphQLResolveInfo], Dict[str, Any]]


class OpenTracingExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _root_scope: Scope
    _tracer: Tracer

    def __init__(self, *, arg_filter: Optional[ArgFilter] = None):
        self._arg_filter = arg_filter
        self._tracer = global_tracer()
        self._root_scope = None

    def on_request_start(self, *, execution_context: ExecutionContext):
        self._root_scope = self._tracer.start_active_span("GraphQL Query")
        self._root_scope.span.set_tag(tags.COMPONENT, "graphql")

    def on_request_end(self, *, execution_context: ExecutionContext):
        self._root_scope.close()

    def filter_resolver_args(
        self, args: Dict[str, Any], info: GraphQLResolveInfo
    ) -> Dict[str, Any]:
        if not self._arg_filter:
            return args
        return self._arg_filter(deepcopy(args), info)

    def get_span(self, scope, info, kwargs):
        span = scope.span
        span.set_tag(tags.COMPONENT, "graphql")
        span.set_tag("graphql.parentType", info.parent_type.name)
        graphql_path = ".".join(map(str, get_path_from_info(info)))
        span.set_tag("graphql.path", graphql_path)
        if kwargs:
            filtered_kwargs = self.filter_resolver_args(kwargs, info)
            for kwarg, value in filtered_kwargs.items():
                span.set_tag(f"graphql.param.{kwarg}", value)

    async def resolve(self, _next, root, info, *args, **kwargs):

        try:
            if not should_trace(info):
                result = _next(root, info, *args, **kwargs)
                if isawaitable(result):
                    result = await result
                return result

            with self._tracer.start_active_span(info.field_name) as scope:
                self.get_span(scope, info, kwargs)
                result = _next(root, info, *args, **kwargs)
                if isawaitable(result):
                    result = await result
                return result
        finally:
            pass


class OpenTracingExtensionSync(OpenTracingExtension):
    def resolve(self, _next, root, info, *args, **kwargs):

        try:
            if not should_trace(info):
                result = _next(root, info, *args, **kwargs)
                return result
            with self._tracer.start_active_span(info.field_name) as scope:
                self.get_span(scope, info, kwargs)
                result = _next(root, info, *args, **kwargs)
                return result

        finally:
            pass
