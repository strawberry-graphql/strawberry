import dataclasses
import time
import typing
from datetime import datetime
from inspect import isawaitable

from strawberry.extensions import Extension
from strawberry.extensions.utils import get_path_from_info
from strawberry.types.execution import ExecutionContext

from .utils import should_skip_tracing


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclasses.dataclass
class ApolloStepStats:
    start_offset: int
    duration: int

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {"startOffset": self.start_offset, "duration": self.duration}


@dataclasses.dataclass
class ApolloResolverStats:
    path: typing.List[str]
    parent_type: typing.Any
    field_name: str
    return_type: typing.Any
    start_offset: int
    duration: typing.Optional[int] = None

    def to_json(self) -> typing.Dict[str, typing.Any]:
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
    resolvers: typing.List[ApolloResolverStats]

    def to_json(self) -> typing.Dict[str, typing.Any]:
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

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "version": self.version,
            "startTime": self.start_time.strftime(DATETIME_FORMAT),
            "endTime": self.end_time.strftime(DATETIME_FORMAT),
            "duration": self.duration,
            "execution": self.execution.to_json(),
            "validation": self.validation.to_json(),
            "parsing": self.parsing.to_json(),
        }


class ApolloTracingExtension(Extension):
    def __init__(self, execution_context: ExecutionContext):
        self._resolver_stats: typing.List[ApolloResolverStats] = []
        self.execution_context = execution_context

    def on_request_start(self):
        self.start_timestamp = self.now()
        self.start_time = datetime.utcnow()

    def on_request_end(self):
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

    def get_results(self):
        return {"tracing": self.stats.to_json()}

    async def resolve(self, _next, root, info, *args, **kwargs):
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
    def resolve(self, _next, root, info, *args, **kwargs):
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
