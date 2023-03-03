import asyncio
import contextlib
import enum
from copy import deepcopy
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.exceptions.exceptions import AlreadyEndedException
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.utils import stacktrace
from graphql import GraphQLResolveInfo

from strawberry.extensions import Extension
from strawberry.extensions.tracing.utils import should_skip_tracing
from strawberry.extensions.utils import get_path_from_info

if TYPE_CHECKING:
    from strawberry.types.execution import ExecutionContext

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

ArgFilter = Callable[[Dict[str, Any], GraphQLResolveInfo], Dict[str, Any]]


class RequestStage(enum.Enum):
    REQUEST = enum.auto()
    PARSING = enum.auto()
    VALIDATION = enum.auto()


class XRayExtension(Extension):
    _arg_filter: Optional[ArgFilter]
    _segment_holder: Dict[RequestStage, Segment] = dict()

    def __init__(
        self,
        *,
        execution_context: Optional["ExecutionContext"] = None,
        arg_filter: Optional[ArgFilter] = None,
    ):
        self._arg_filter = arg_filter
        if execution_context:
            self.execution_context = execution_context

    def on_request_start(self):
        self._operation_name = self.execution_context.operation_name
        segment_name = (
            f"GraphQL Query: {self._operation_name}"
            if self._operation_name
            else "GraphQL Query"
        )

        self._segment_holder[RequestStage.REQUEST] = xray_recorder.begin_subsegment(
            name=segment_name
        )
        if self._segment_holder.get(RequestStage.REQUEST) is not None:
            self._segment_holder[RequestStage.REQUEST].put_annotation(
                "component", "graphql"
            )

            if self.execution_context.query:
                self._segment_holder[RequestStage.REQUEST].put_annotation(
                    "query", self.execution_context.query
                )

    def on_request_end(self):
        # If the client doesn't provide an operation name then GraphQL will
        # execute the first operation in the query string. This might be a named
        # operation but we don't know until the parsing stage has finished. If
        # that's the case we want to update the segment name so that we have a more
        # useful name in our trace.

        if (
            not self._operation_name
            and self.execution_context.operation_name
            and self._segment_holder.get(RequestStage.REQUEST) is not None
        ):
            segment_name = f"GraphQL Query: {self.execution_context.operation_name}"
            self._segment_holder[RequestStage.REQUEST].name = segment_name

        result = self.execution_context.result
        errors = getattr(result, "errors", [])
        if self._segment_holder.get(RequestStage.REQUEST) is not None and errors:
            stack = stacktrace.get_stacktrace(limit=xray_recorder.max_trace_back)
            for error in errors:
                self._segment_holder[RequestStage.REQUEST].add_exception(
                    error.original_error, stack
                )
        if self._segment_holder.get(RequestStage.REQUEST) is not None:
            with contextlib.suppress(AlreadyEndedException):
                self._segment_holder[
                    RequestStage.REQUEST
                ] = xray_recorder.end_subsegment()

    def on_validation_start(self):
        if self._segment_holder.get(RequestStage.VALIDATION) is not None:
            self._segment_holder[
                RequestStage.VALIDATION
            ] = xray_recorder.begin_subsegment("GraphQL Validation")

    def on_validation_end(self):
        if self._segment_holder.get(RequestStage.VALIDATION) is not None:
            self._segment_holder[
                RequestStage.VALIDATION
            ] = xray_recorder.end_subsegment()

    def on_parsing_start(self):
        if self._segment_holder.get(RequestStage.PARSING) is not None:
            self._segment_holder[RequestStage.PARSING] = xray_recorder.begin_subsegment(
                "GraphQL Parsing"
            )

    def on_parsing_end(self):
        if self._segment_holder.get(RequestStage.PARSING) is not None:
            self._segment_holder[RequestStage.PARSING] = xray_recorder.end_subsegment()

    def filter_resolver_args(
        self, args: Dict[str, Any], info: GraphQLResolveInfo
    ) -> Dict[str, Any]:
        return self._arg_filter(deepcopy(args), info) if self._arg_filter else args

    async def add_tags(
        self, segment: Segment, info: GraphQLResolveInfo, kwargs: Dict[str, Any]
    ):
        graphql_path = ".".join(map(str, get_path_from_info(info)))

        await segment.put_annotation("component", "graphql")
        await segment.put_annotation("graphql_parentType", info.parent_type.name)
        await segment.put_annotation("graphql_path", graphql_path)

        if kwargs:
            filtered_kwargs = self.filter_resolver_args(kwargs, info)

            for kwarg, value in filtered_kwargs.items():
                await segment.put_metadata(f"graphql_param_{kwarg}", value)

    async def resolve(self, _next, root, info, *args, **kwargs):
        if should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):  # pragma: no cover
                result = await result

            return result

        async with xray_recorder.in_subsegment_async(
            f"GraphQL Resolving: {info.field_name}"
        ) as subsegment:
            if subsegment is not None:
                await self.add_tags(subsegment, info, kwargs)
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result


class XRayExtensionSync(XRayExtension):
    def resolve(self, _next, root, info, *args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(
            super().resolve(_next, root, info, *args, **kwargs)
        )
