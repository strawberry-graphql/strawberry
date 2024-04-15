from __future__ import annotations

import dataclasses
import time
from datetime import datetime, timezone
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, List, Optional

from strawberry.extensions import SchemaExtension
from strawberry.extensions.utils import get_path_from_info

from .utils import should_skip_tracing

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

if TYPE_CHECKING:
    from strawberry.types.execution import ExecutionContext


@dataclasses.dataclass
class ApolloStepStats:
    start_offset: int
    duration: int

    def to_json(self) -> Dict[str, Any]:
        return {"startOffset": self.start_offset, "duration": self.duration}


@dataclasses.dataclass
class ApolloResolverStats:
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
class ApolloExecutionStats:
    resolvers: List[ApolloResolverStats]

    def to_json(self) -> Dict[str, Any]:
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


class ApolloTracingExtension(SchemaExtension):
    def __init__(self, execution_context: ExecutionContext) -> None:
        self._resolver_stats: List[ApolloResolverStats] = []
        self.execution_context = execution_context

    def on_operation(self) -> Generator[None, None, None]:
        self.start_timestamp = self.now()
        self.start_time = datetime.now(timezone.utc)
        yield
        self.end_timestamp = self.now()
        self.end_time = datetime.now(timezone.utc)

    def on_parse(self) -> Generator[None, None, None]:
        self._start_parsing = self.now()
        yield
        self._end_parsing = self.now()

    def on_validate(self) -> Generator[None, None, None]:
        self._start_validation = self.now()
        yield
        self._end_validation = self.now()

    def now(self) -> int:
        return time.perf_counter_ns()

    @property
    def stats(self) -> ApolloTracingStats:
        return ApolloTracingStats(
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.end_timestamp - self.start_timestamp,
            execution=ApolloExecutionStats(self._resolver_stats),
            validation=ApolloStepStats(
                start_offset=self._start_validation - self.start_timestamp,
                duration=self._end_validation - self._start_validation,
            ),
            parsing=ApolloStepStats(
                start_offset=self._start_parsing - self.start_timestamp,
                duration=self._end_parsing - self._start_parsing,
            ),
        )

    def get_results(self) -> Dict[str, Dict[str, Any]]:
        return {"tracing": self.stats.to_json()}

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

        start_timestamp = self.now()

        resolver_stats = ApolloResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - self.start_timestamp,
        )

        try:
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result
        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            self._resolver_stats.append(resolver_stats)


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

        start_timestamp = self.now()

        resolver_stats = ApolloResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - self.start_timestamp,
        )

        try:
            return _next(root, info, *args, **kwargs)
        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            self._resolver_stats.append(resolver_stats)
