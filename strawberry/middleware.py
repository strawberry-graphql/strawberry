import asyncio
import time
from abc import abstractmethod
from typing import Any, Dict, List

from typing_extensions import Protocol

from .directive import DirectiveDefinition


SPECIFIED_DIRECTIVES = {"include", "skip"}


class Middleware(Protocol):
    @abstractmethod
    def resolve(self, next_, root, info, **kwargs):
        raise NotImplementedError


class DirectivesMiddleware:
    def __init__(self, directives: List[Any]):
        self.directives: Dict[str, DirectiveDefinition] = {
            directive.directive_definition.name: directive.directive_definition
            for directive in directives
        }

    def resolve(self, next_, root, info, **kwargs):
        result = next_(root, info, **kwargs)

        for directive in info.field_nodes[0].directives:
            directive_name = directive.name.value

            if directive_name in SPECIFIED_DIRECTIVES:
                continue

            func = self.directives[directive_name].resolver

            # TODO: support converting lists

            arguments = {
                argument.name.value: argument.value.value
                for argument in directive.arguments
            }

            result = func(result, **arguments)

        return result


# TODO: ?

class TracingMiddleware:
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self):
        self.resolver_stats = list()
        self.start_time = None
        self.end_time = None
        self.parsing_start_time = None
        self.parsing_end_time = None
        self.validation_start_time = None
        self.validation_end_time = None

    def start(self):
        self.start_time = self.now()

    def end(self):
        self.end_time = self.now()

    def parsing_start(self):
        self.parsing_start_time = self.now()

    def parsing_end(self):
        self.parsing_end_time = self.now()

    def validation_start(self):
        self.validation_start_time = self.now()

    def validation_end(self):
        self.validation_end_time = self.now()

    def now(self):
        return time.time_ns()

    @property
    def start_time_str(self):
        return time.strftime(self.DATETIME_FORMAT, time.gmtime(self.start_time / 1000))

    @property
    def end_time_str(self):
        return time.strftime(self.DATETIME_FORMAT, time.gmtime(self.end_time / 1000))

    @property
    def duration(self):
        if not self.end_time:
            raise ValueError("Tracing has not ended yet!")

        return self.end_time - self.start_time

    @property
    def tracing_dict(self):
        result = dict(
            version=1,
            startTime=self.start_time_str,
            endTime=self.end_time_str,
            duration=self.duration,
            execution=dict(resolvers=self.resolver_stats),
        )

        if self.parsing_start_time and self.parsing_end_time:
            result["parsing"] = dict(
                startOffset=self.parsing_start_time - self.start_time,
                duration=self.parsing_end_time - self.parsing_start_time,
            )

        if self.validation_start_time and self.validation_end_time:
            result["validation"] = dict(
                startOffset=self.validation_start_time - self.start_time,
                duration=self.validation_end_time - self.validation_start_time,
            )

        return result

    async def resolve(self, _next, root, info, *args, **kwargs):
        start = self.now()
        try:
            return_value = _next(root, info, *args, **kwargs)

            if asyncio.iscoroutine(return_value):
                return await return_value
            else:
                return return_value
        finally:
            end = self.now()
            elapsed_ns = end - start

            stat = {
                "path": info.path,
                "parentType": str(info.parent_type),
                "fieldName": info.field_name,
                "returnType": str(info.return_type),
                "startOffset": self.now() - self.start_time,
                "duration": elapsed_ns,
            }
            self.resolver_stats.append(stat)
