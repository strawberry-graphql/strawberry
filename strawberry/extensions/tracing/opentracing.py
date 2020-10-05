import dataclasses
import time
from copy import deepcopy
from datetime import datetime
from inspect import isawaitable
from typing import Any, Callable, Dict, List, Optional

from graphql import GraphQLResolveInfo
from opentracing import Scope, Tracer, global_tracer
from opentracing.ext import tags
from strawberry.extensions import Extension
from strawberry.types.execution import ExecutionContext
from strawberry.utils.info import get_path_from_info

from .utils import should_trace


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

ArgFilter = Callable[[Dict[str, Any], GraphQLResolveInfo], Dict[str, Any]]


@dataclasses.dataclass
class OpenTracingStepStats:
    start_offset: int
    duration: int

    def to_json(self) -> Dict[str, Any]:
        return {"startOffset": self.start_offset, "duration": self.duration}


@dataclasses.dataclass
class OpenTracingResolverStats:
    path: List[str]
    parent_type: Any
    field_name: str
    return_type: Any
    start_offset: int
    duration: Optional[int] = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "field_name": self.field_name,
            "parentType": str(self.parent_type),
            "returnType": str(self.return_type),
            "startOffset": self.start_offset,
            "duration": self.duration,
        }


@dataclasses.dataclass
class OpenTracingExecutionStats:
    resolvers: List[OpenTracingResolverStats]

    def to_json(self) -> Dict[str, Any]:
        return {"resolvers": [resolver.to_json() for resolver in self.resolvers]}


@dataclasses.dataclass
class OpenTracingStats:
    start_time: datetime
    end_time: datetime
    duration: int
    execution: OpenTracingExecutionStats
    validation: OpenTracingStepStats
    parsing: OpenTracingStepStats
    version: int = 1

    def to_json(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "startTime": self.start_time.strftime(DATETIME_FORMAT),
            "endTime": self.end_time.strftime(DATETIME_FORMAT),
            "duration": self.duration,
            "execution": self.execution.to_json(),
            "validation": self.validation.to_json(),
            "parsing": self.parsing.to_json(),
        }


class OpenTracingExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _root_scope: Scope
    _tracer: Tracer

    def __init__(self):
        self._tracer = global_tracer()
        self._root_scope = None
        self._resolver_stats: List[OpenTracingResolverStats] = []

    def on_request_start(self, *, execution_context: ExecutionContext):
        self.start_timestamp = self.now()
        self.start_time = datetime.utcnow()
        self._root_scope = self._tracer.start_active_span("GraphQL Query")
        self._root_scope.span.set_tag(tags.COMPONENT, "graphql")

    def on_request_end(self, *, execution_context: ExecutionContext):
        self._root_scope.close()
        self.end_timestamp = self.now()
        self.end_time = datetime.utcnow()

    def on_parsing_start(self):
        self._start_parsing = self.now()

    def on_parsing_end(self):
        self._end_parsing = self.now()

    def on_validation_start(self):
        self._start_validation = self.now()

    def on_validation_end(self):
        self._end_validation = self.now()

    def now(self) -> int:
        return time.perf_counter_ns()

    @property
    def stats(self) -> OpenTracingStats:
        return OpenTracingStats(
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.end_timestamp - self.start_timestamp,
            execution=OpenTracingExecutionStats(self._resolver_stats),
            validation=OpenTracingStepStats(
                start_offset=self._start_validation - self.start_timestamp,
                duration=self._end_validation - self._start_validation,
            ),
            parsing=OpenTracingStepStats(
                start_offset=self._start_parsing - self.start_timestamp,
                duration=self._end_parsing - self._start_parsing,
            ),
        )

    def get_results(self):
        return {"tracing": self.stats.to_json()}

    def filter_resolver_args(
        self, args: Dict[str, Any], info: GraphQLResolveInfo
    ) -> Dict[str, Any]:
        if not self._arg_filter:
            return args
        return self._arg_filter(deepcopy(args), info)

    async def resolve(self, _next, root, info, *args, **kwargs):
        start_timestamp = self.now()

        resolver_stats = OpenTracingResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - self.start_timestamp,
        )

        try:
            if not should_trace(info):
                result = _next(root, info, *args, **kwargs)
                if isawaitable(result):
                    result = await result
                return result

            with self._tracer.start_active_span(info.field_name) as scope:
                span = scope.span
                span.set_tag(tags.COMPONENT, "graphql")
                span.set_tag("graphql.parentType", info.parent_type.name)

                graphql_path = ".".join(map(str, get_path_from_info(info)))
                span.set_tag("graphql.path", graphql_path)
                if kwargs:
                    filtered_kwargs = self.filter_resolver_args(kwargs, info)
                    for kwarg, value in filtered_kwargs.items():
                        span.set_tag(f"graphql.param.{kwarg}", value)

                result = _next(root, info, *args, **kwargs)

                if isawaitable(result):
                    result = await result
                return result
        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            self._resolver_stats.append(resolver_stats)


class OpenTracingExtensionSync(OpenTracingExtension):
    def resolve(self, _next, root, info, *args, **kwargs):
        start_timestamp = self.now()

        resolver_stats = OpenTracingResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - self.start_timestamp,
        )

        try:
            if not should_trace(info):
                result = _next(root, info, *args, **kwargs)
                return result
            with self._tracer.start_active_span(info.field_name) as scope:
                span = scope.span
                span.set_tag(tags.COMPONENT, "graphql")
                span.set_tag("graphql.parentType", info.parent_type.name)

                graphql_path = ".".join(map(str, get_path_from_info(info)))
                span.set_tag("graphql.path", graphql_path)

                if kwargs:
                    filtered_kwargs = self.filter_resolver_args(kwargs, info)
                    for kwarg, value in filtered_kwargs.items():
                        span.set_tag(f"graphql.param.{kwarg}", value)

                result = _next(root, info, *args, **kwargs)
                return result

        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            self._resolver_stats.append(resolver_stats)
