import dataclasses
import time
import typing
from datetime import datetime
from inspect import isawaitable

from graphql import GraphQLResolveInfo


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def get_path_from_info(info: GraphQLResolveInfo) -> typing.List[str]:
    path = info.path
    elements = []

    while path:
        elements.append(path.key)
        path = path.prev

    return elements[::-1]


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


class SyncTracingMiddleware:
    def __init__(self):
        self._resolver_stats: typing.List[ApolloResolverStats] = []

    def start(self):
        self._start_timestamp = self.now()
        self._start_time = datetime.utcnow()

    def stop(self):
        self._end_timestamp = self.now()
        self._end_time = datetime.utcnow()

    def start_parsing(self):
        self._start_parsing = self.now()

    def end_parsing(self):
        self._end_parsing = self.now()

    def start_validation(self):
        self._start_validation = self.now()

    def end_validation(self):
        self._end_validation = self.now()

    def now(self) -> int:
        return time.perf_counter_ns()

    @property
    def stats(self) -> ApolloTracingStats:
        return ApolloTracingStats(
            start_time=self._start_time,
            end_time=self._end_time,
            duration=self._end_timestamp - self._start_timestamp,
            execution=ApolloExecutionStats(self._resolver_stats),
            validation=ApolloStepStats(
                start_offset=self._start_validation - self._start_timestamp,
                duration=self._end_validation - self._start_validation,
            ),
            parsing=ApolloStepStats(
                start_offset=self._start_parsing - self._start_timestamp,
                duration=self._end_parsing - self._start_parsing,
            ),
        )

    def resolve(self, _next, root, info, *args, **kwargs):
        start_timestamp = self.now()

        resolver_stats = ApolloResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - self._start_timestamp,
        )

        try:
            return _next(root, info, *args, **kwargs)
        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            self._resolver_stats.append(resolver_stats)


class TracingMiddleware(SyncTracingMiddleware):
    async def resolve(self, _next, root, info, *args, **kwargs):
        start_timestamp = self.now()

        resolver_stats = ApolloResolverStats(
            path=get_path_from_info(info),
            field_name=info.field_name,
            parent_type=info.parent_type,
            return_type=info.return_type,
            start_offset=start_timestamp - self._start_timestamp,
        )

        try:
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                return await result

            return result
        finally:
            end_timestamp = self.now()
            resolver_stats.duration = end_timestamp - start_timestamp
            self._resolver_stats.append(resolver_stats)
