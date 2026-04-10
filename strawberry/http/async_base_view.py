import abc
import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncGenerator, Callable, Mapping
from datetime import timedelta
from typing import (
    Any,
    Generic,
    TypeGuard,
    cast,
    overload,
)

from cross_web import AsyncHTTPRequestAdapter, HTTPException
from graphql import GraphQLError

from strawberry.exceptions import ConnectionRejectionError, MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import (
    GraphQLHTTPResponse,
    GraphQLRequestData,
    GraphQLSubscriptionProtocol,
    process_result,
)
from strawberry.http.ides import GraphQL_IDE
from strawberry.schema._graphql_core import (
    GraphQLIncrementalExecutionResults,
)
from strawberry.schema.base import BaseSchema
from strawberry.schema.exceptions import (
    CannotGetOperationTypeError,
    InvalidOperationTypeError,
)
from strawberry.subscriptions import (
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
)
from strawberry.subscriptions.protocols.graphql_transport_ws.handlers import (
    BaseGraphQLTransportWSHandler,
)
from strawberry.subscriptions.protocols.graphql_ws.handlers import BaseGraphQLWSHandler
from strawberry.types import (
    ExecutionResult,
    PreExecutionError,
    SubscriptionExecutionResult,
)
from strawberry.types.graphql import OperationType
from strawberry.types.unset import UNSET, UnsetType

from .base import BaseView
from .parse_content_type import parse_content_type
from .typevars import (
    Context,
    Request,
    Response,
    RootValue,
    SubResponse,
    WebSocketRequest,
    WebSocketResponse,
)

_sse_http1_warning_logged = False


class AsyncWebSocketAdapter(abc.ABC):
    def __init__(self, view: "AsyncBaseHTTPView") -> None:
        self.view = view

    @abc.abstractmethod
    def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]: ...

    @abc.abstractmethod
    async def send_json(self, message: Mapping[str, object]) -> None: ...

    @abc.abstractmethod
    async def close(self, code: int, reason: str) -> None: ...


class AsyncBaseHTTPView(
    abc.ABC,
    BaseView[Request],
    Generic[
        Request,
        Response,
        SubResponse,
        WebSocketRequest,
        WebSocketResponse,
        Context,
        RootValue,
    ],
):
    schema: BaseSchema
    graphql_ide: GraphQL_IDE | None
    keep_alive = False
    keep_alive_interval: float | None = None
    connection_init_wait_timeout: timedelta = timedelta(minutes=1)
    max_subscriptions_per_connection: int | None = 100
    sse_heartbeat_interval: float = 5.0
    sse_queue_buffer_size: int = 1
    sse_enabled: bool = False
    request_adapter_class: Callable[[Request], AsyncHTTPRequestAdapter]
    websocket_adapter_class: Callable[
        [
            "AsyncBaseHTTPView[Any, Any, Any, Any, Any, Context, RootValue]",
            WebSocketRequest,
            WebSocketResponse,
        ],
        AsyncWebSocketAdapter,
    ]
    graphql_transport_ws_handler_class: type[
        BaseGraphQLTransportWSHandler[Context, RootValue]
    ] = BaseGraphQLTransportWSHandler[Context, RootValue]
    graphql_ws_handler_class: type[BaseGraphQLWSHandler[Context, RootValue]] = (
        BaseGraphQLWSHandler[Context, RootValue]
    )

    @property
    @abc.abstractmethod
    def allow_queries_via_get(self) -> bool: ...

    @abc.abstractmethod
    async def get_sub_response(self, request: Request) -> SubResponse: ...

    @abc.abstractmethod
    async def get_context(
        self,
        request: Request | WebSocketRequest,
        response: SubResponse | WebSocketResponse,
    ) -> Context: ...

    @abc.abstractmethod
    async def get_root_value(
        self, request: Request | WebSocketRequest
    ) -> RootValue | None: ...

    @abc.abstractmethod
    def create_response(
        self,
        response_data: GraphQLHTTPResponse | list[GraphQLHTTPResponse],
        sub_response: SubResponse,
    ) -> Response: ...

    @abc.abstractmethod
    async def render_graphql_ide(self, request: Request) -> Response: ...

    async def create_streaming_response(
        self,
        request: Request,
        stream: Callable[[], AsyncGenerator[str, None]],
        sub_response: SubResponse,
        headers: dict[str, str],
    ) -> Response:
        raise ValueError("Multipart responses are not supported")

    @abc.abstractmethod
    def is_websocket_request(
        self, request: Request | WebSocketRequest
    ) -> TypeGuard[WebSocketRequest]: ...

    @abc.abstractmethod
    async def pick_websocket_subprotocol(
        self, request: WebSocketRequest
    ) -> str | None: ...

    @abc.abstractmethod
    async def create_websocket_response(
        self, request: WebSocketRequest, subprotocol: str | None
    ) -> WebSocketResponse: ...

    @staticmethod
    def _is_subscription_operation(
        query: str, operation_name: str | None = None
    ) -> bool:
        """Check if a GraphQL query is a subscription using lightweight lexing.

        Uses graphql-core's Lexer to scan only the tokens needed to determine
        the operation type, avoiding a full AST parse. For unnamed operations,
        this reads just 1-2 tokens. For named operations, it scans until it
        finds the matching definition.
        """
        from graphql.language import Lexer, Source, TokenKind

        try:
            lexer = Lexer(Source(query))
            token = lexer.advance()

            if operation_name is None:
                # Unnamed/first operation or shorthand query
                if token.kind == TokenKind.BRACE_L:
                    return False  # shorthand query: { field }
                if token.kind == TokenKind.NAME:
                    return token.value == "subscription"
                return False

            # Named operation: scan for matching definition
            while token.kind != TokenKind.EOF:
                if token.kind == TokenKind.NAME and token.value in (
                    "query",
                    "mutation",
                    "subscription",
                ):
                    op_type_value = token.value
                    next_token = lexer.advance()
                    if (
                        next_token.kind == TokenKind.NAME
                        and next_token.value == operation_name
                    ):
                        return op_type_value == "subscription"
                token = lexer.advance()
        except (GraphQLError, TypeError, ValueError):
            # GraphQLError (including GraphQLSyntaxError) for malformed queries,
            # TypeError/ValueError for invalid input types.
            # If we can't determine the type, default to non-subscription
            # and let the normal execution path handle the error properly.
            pass

        return False

    async def execute_operation(
        self,
        request: Request,
        context: Context,
        root_value: RootValue | None,
        sub_response: SubResponse,
    ) -> (
        ExecutionResult
        | list[ExecutionResult]
        | SubscriptionExecutionResult
        | AsyncGenerator[PreExecutionError | ExecutionResult, None]
    ):
        request_adapter = self.request_adapter_class(request)

        try:
            request_data = await self.parse_http_body(request_adapter)
        except json.decoder.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e
            # DO this only when doing files
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

        allowed_operation_types = OperationType.from_http(request_adapter.method)

        if not self.allow_queries_via_get and request_adapter.method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        if isinstance(request_data, list):
            # batch GraphQL requests
            return await asyncio.gather(
                *[
                    self.execute_single(
                        request=request,
                        request_adapter=request_adapter,
                        sub_response=sub_response,
                        context=context,
                        root_value=root_value,
                        request_data=data,
                    )
                    for data in request_data
                ]
            )

        if request_data.protocol in (
            GraphQLSubscriptionProtocol.MULTIPART_SUBSCRIPTION,
            GraphQLSubscriptionProtocol.GRAPHQL_SSE,
        ):
            if not request_data.query:
                raise HTTPException(400, 'Request data is missing a "query" value')

            # For SSE, only route subscriptions through subscribe().
            # Queries and mutations should use the normal execution path.
            if (
                request_data.protocol == GraphQLSubscriptionProtocol.GRAPHQL_SSE
                and not self._is_subscription_operation(
                    request_data.query, request_data.operation_name
                )
            ):
                return await self.execute_single(
                    request=request,
                    request_adapter=request_adapter,
                    sub_response=sub_response,
                    context=context,
                    root_value=root_value,
                    request_data=request_data,
                )

            return await self.schema.subscribe(
                request_data.query,
                variable_values=request_data.variables,
                context_value=context,
                root_value=root_value,
                operation_name=request_data.operation_name,
                operation_extensions=request_data.extensions,
            )

        return await self.execute_single(
            request=request,
            request_adapter=request_adapter,
            sub_response=sub_response,
            context=context,
            root_value=root_value,
            request_data=request_data,
        )

    async def execute_single(
        self,
        request: Request,
        request_adapter: AsyncHTTPRequestAdapter,
        sub_response: SubResponse,
        context: Context,
        root_value: RootValue | None,
        request_data: GraphQLRequestData,
    ) -> ExecutionResult:
        allowed_operation_types = OperationType.from_http(request_adapter.method)

        if not self.allow_queries_via_get and request_adapter.method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        try:
            result = await self.schema.execute(
                request_data.query,
                root_value=root_value,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                allowed_operation_types=allowed_operation_types,
                operation_extensions=request_data.extensions,
            )
        except CannotGetOperationTypeError as e:
            raise HTTPException(400, e.as_http_error_reason()) from e
        except InvalidOperationTypeError as e:
            raise HTTPException(
                400, e.as_http_error_reason(request_adapter.method)
            ) from e
        except MissingQueryError as e:
            raise HTTPException(400, "No GraphQL query found in the request") from e

        return result

    async def parse_multipart(self, request: AsyncHTTPRequestAdapter) -> dict[str, str]:
        try:
            form_data = await request.get_form_data()
        except ValueError as e:
            raise HTTPException(400, "Unable to parse the multipart body") from e

        operations = form_data.form.get("operations", "{}")
        files_map = form_data.form.get("map", "{}")
        files = form_data.files

        if isinstance(operations, (bytes, str)):
            operations = self.parse_json(operations)

        if isinstance(files_map, (bytes, str)):
            files_map = self.parse_json(files_map)

        try:
            return replace_placeholders_with_files(operations, files_map, files)
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

    def _handle_errors(
        self, errors: list[GraphQLError], response_data: GraphQLHTTPResponse
    ) -> None:
        """Hook to allow custom handling of errors, used by the Sentry Integration."""

    @overload
    async def run(
        self,
        request: Request,
        context: Context = UNSET,
        root_value: RootValue | None = UNSET,
    ) -> Response: ...

    @overload
    async def run(
        self,
        request: WebSocketRequest,
        context: Context = UNSET,
        root_value: RootValue | None = UNSET,
    ) -> WebSocketResponse: ...

    async def run(
        self,
        request: Request | WebSocketRequest,
        context: Context = UNSET,
        root_value: RootValue | None = UNSET,
    ) -> Response | WebSocketResponse:
        root_value = (
            await self.get_root_value(request) if root_value is UNSET else root_value
        )

        if self.is_websocket_request(request):
            websocket_subprotocol = await self.pick_websocket_subprotocol(request)
            websocket_response = await self.create_websocket_response(
                request, websocket_subprotocol
            )
            websocket = self.websocket_adapter_class(self, request, websocket_response)

            context = (
                await self.get_context(request, response=websocket_response)
                if context is UNSET
                else context
            )

            if websocket_subprotocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
                await self.graphql_transport_ws_handler_class(
                    view=self,
                    websocket=websocket,
                    context=context,
                    root_value=root_value,
                    schema=self.schema,
                    connection_init_wait_timeout=self.connection_init_wait_timeout,
                    max_subscriptions_per_connection=self.max_subscriptions_per_connection,
                ).handle()
            elif websocket_subprotocol == GRAPHQL_WS_PROTOCOL:
                await self.graphql_ws_handler_class(
                    view=self,
                    websocket=websocket,
                    context=context,
                    root_value=root_value,
                    schema=self.schema,
                    keep_alive=self.keep_alive,
                    keep_alive_interval=self.keep_alive_interval,
                    max_subscriptions_per_connection=self.max_subscriptions_per_connection,
                ).handle()
            else:
                await websocket.close(4406, "Subprotocol not acceptable")

            return websocket_response
        request = cast("Request", request)

        request_adapter = self.request_adapter_class(request)
        sub_response = await self.get_sub_response(request)
        context = (
            await self.get_context(request, response=sub_response)
            if context is UNSET
            else context
        )

        if not self.is_request_allowed(request_adapter):
            raise HTTPException(405, "GraphQL only supports GET and POST requests.")

        if self.should_render_graphql_ide(request_adapter):
            if self.graphql_ide:
                return await self.render_graphql_ide(request)
            raise HTTPException(404, "Not Found")

        result = await self.execute_operation(
            request=request,
            context=context,
            root_value=root_value,
            sub_response=sub_response,
        )

        if isinstance(result, SubscriptionExecutionResult):
            accept = {
                key.lower(): value for key, value in request_adapter.headers.items()
            }.get("accept", "")

            if self._is_sse_subscription(accept):
                self._warn_if_http1_for_sse(request)
                last_event_id = self._get_last_event_id(request_adapter)
                try:
                    await self.on_sse_connect(context)
                except ConnectionRejectionError as e:
                    if e.payload:
                        error_response = e.payload
                    else:
                        error_response = {"message": "Forbidden", "code": "FORBIDDEN"}
                    return await self._create_sse_error_response(
                        request,
                        sub_response,
                        str(error_response.get("code", "FORBIDDEN")),
                        str(error_response.get("message", "Forbidden")),
                    )
                stream = self._get_sse_stream(request, result, last_event_id)

                return await self.create_streaming_response(
                    request,
                    stream,
                    sub_response,
                    headers={
                        "Content-Type": "text/event-stream",
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    },
                )

            stream = self._get_stream(request, result)

            return await self.create_streaming_response(
                request,
                stream,
                sub_response,
                headers={
                    "Content-Type": "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json",
                },
            )
        if isinstance(result, GraphQLIncrementalExecutionResults):

            async def stream() -> AsyncGenerator[str, None]:
                yield "---"

                response = await self.process_result(request, result.initial_result)

                response["hasNext"] = result.initial_result.has_next
                response["pending"] = [
                    p.formatted for p in result.initial_result.pending
                ]
                response["extensions"] = result.initial_result.extensions

                yield self.encode_multipart_data(response, "-")

                all_pending = result.initial_result.pending

                async for value in result.subsequent_results:
                    response = {
                        "hasNext": value.has_next,
                        "extensions": value.extensions,
                    }

                    if value.pending:
                        response["pending"] = [p.formatted for p in value.pending]

                    if value.completed:
                        response["completed"] = [p.formatted for p in value.completed]

                    if value.incremental:
                        incremental = []

                        all_pending.extend(value.pending)

                        for incremental_value in value.incremental:
                            pending_value = next(
                                (
                                    v
                                    for v in all_pending
                                    if v.id == incremental_value.id
                                ),
                                None,
                            )

                            assert pending_value

                            incremental.append(
                                {
                                    **incremental_value.formatted,
                                    "path": pending_value.path,
                                    "label": pending_value.label,
                                }
                            )

                        response["incremental"] = incremental

                    yield self.encode_multipart_data(response, "-")

                yield "--\r\n"

            return await self.create_streaming_response(
                request,
                stream,
                sub_response,
                headers={
                    "Content-Type": 'multipart/mixed; boundary="-"',
                },
            )

        response_data: GraphQLHTTPResponse | list[GraphQLHTTPResponse]

        if isinstance(result, list):
            response_data = []
            for execution_result in result:
                processed_result = await self.process_result(
                    request=request, result=execution_result
                )
                if execution_result.errors:
                    self._handle_errors(execution_result.errors, processed_result)
                response_data.append(processed_result)
        else:
            result_cast = cast("ExecutionResult", result)
            response_data = await self.process_result(
                request=request, result=result_cast
            )

            if result_cast.errors:
                self._handle_errors(result_cast.errors, response_data)

        return self.create_response(
            response_data=response_data, sub_response=sub_response
        )

    def encode_multipart_data(self, data: Any, separator: str) -> str:
        encoded_data = self.encode_json(data)
        if isinstance(encoded_data, bytes):
            encoded_data = encoded_data.decode()
        return "".join(
            [
                "\r\n",
                "Content-Type: application/json; charset=utf-8\r\n",
                "Content-Length: " + str(len(encoded_data)) + "\r\n",
                "\r\n",
                encoded_data,
                f"\r\n--{separator}",
            ]
        )

    def _stream_with_heartbeat(
        self, stream: Callable[[], AsyncGenerator[str, None]], separator: str
    ) -> Callable[[], AsyncGenerator[str, None]]:
        """Add heartbeat messages to a GraphQL stream to prevent connection timeouts.

        This method wraps an async stream generator with heartbeat functionality by:
        1. Creating a queue to coordinate between data and heartbeat messages
        2. Running two concurrent tasks: one for original stream data, one for heartbeats
        3. Merging both message types into a single output stream

        Messages in the queue are tuples of (raised, done, data) where:
        - raised (bool): True if this contains an exception to be re-raised
        - done (bool): True if this is the final signal indicating stream completion
        - data: The actual message content to yield, or exception if raised=True
               Note: data is always None when done=True and can be ignored

        Note: This implementation addresses two critical concerns:

        1. Race condition: There's a potential race between checking task.done() and
           processing the final message. We solve this by having the drain task send
           an explicit (False, True, None) completion signal as its final action.
           Without this signal, we might exit before processing the final boundary.

           Since the queue size is 1 and the drain task will only complete after
           successfully queueing the done signal, task.done() guarantees the done
           signal is either in the queue or has already been processed. This ensures
           we never miss the final boundary.

        2. Flow control: The queue has maxsize=1, which is essential because:
           - It provides natural backpressure between producers and consumer
           - Prevents heartbeat messages from accumulating when drain is active
           - Ensures proper task coordination without complex synchronization
           - Guarantees the done signal is queued before drain task completes

        Heartbeats are sent every 5 seconds when the drain task isn't sending data.

        Note: Due to the asynchronous nature of the heartbeat task, an extra heartbeat
        message may be sent after the final stream boundary message. This is safe because
        both the MIME specification (RFC 2046) and Apollo's GraphQL Multipart HTTP protocol
        require clients to ignore any content after the final boundary marker. Additionally,
        Apollo's protocol defines heartbeats as empty JSON objects that clients must
        silently ignore.
        """
        return self._make_heartbeat_stream(
            stream,
            heartbeat_message_provider=lambda: self.encode_multipart_data(
                {}, separator
            ),
        )

    def _get_stream(
        self,
        request: Request,
        result: SubscriptionExecutionResult,
        separator: str = "graphql",
    ) -> Callable[[], AsyncGenerator[str, None]]:
        async def stream() -> AsyncGenerator[str, None]:
            async for value in result:
                response = await self.process_result(request, value)
                yield self.encode_multipart_data({"payload": response}, separator)

            yield f"\r\n--{separator}--\r\n"

        return self._stream_with_heartbeat(stream, separator)

    def encode_sse_event(
        self, event: str, data: Any = None, event_id: int | None = None
    ) -> str:
        """Encode a Server-Sent Event message.

        Format per SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html
        When data is None, an empty data field is included (required for
        EventSource clients to trigger event listeners).

        Args:
            event: The event type (e.g., "next", "complete", "error")
            data: The event data to encode as JSON
            event_id: Optional numeric ID for Last-Event-ID header support
        """
        id_line = f"id: {event_id}\n" if event_id is not None else ""
        if data is None:
            return f"{id_line}event: {event}\ndata:\n\n"
        encoded_data = self.encode_json(data)
        if isinstance(encoded_data, bytes):
            encoded_data = encoded_data.decode()
        return f"{id_line}event: {event}\ndata: {encoded_data}\n\n"

    def _get_sse_stream(
        self,
        request: Request,
        result: SubscriptionExecutionResult,
        last_event_id: int | None = None,
    ) -> Callable[[], AsyncGenerator[str, None]]:
        event_counter = last_event_id or 0

        async def stream() -> AsyncGenerator[str, None]:
            nonlocal event_counter
            try:
                async for value in result:
                    event_counter += 1
                    response = await self.process_result(request, value)
                    yield self.encode_sse_event(
                        "next", {"payload": response}, event_id=event_counter
                    )
            except Exception as exc:  # noqa: BLE001
                event_counter += 1
                yield self.encode_sse_event(
                    "error",
                    [{"message": str(exc)}],
                    event_id=event_counter,
                )
                return
            event_counter += 1
            yield self.encode_sse_event("complete", event_id=event_counter)

        return self._stream_sse_with_heartbeat(stream)

    def _get_http_version(self, request: Request) -> str | None:
        """Extract HTTP version from the request.

        For ASGI apps (Starlette, FastAPI, etc.), the request has a scope dict
        containing the HTTP version as a string (e.g., "1.1", "2.0").

        For aiohttp, the request has a version attribute which is a tuple
        (e.g., (1, 1) for HTTP/1.1, (2, 0) for HTTP/2).

        Returns None if the HTTP version cannot be determined.
        """
        if hasattr(request, "scope") and isinstance(request.scope, dict):
            return request.scope.get("http_version")
        if hasattr(request, "version"):
            version = request.version
            if isinstance(version, tuple) and len(version) >= 1:
                return f"{version[0]}.{version[1] if len(version) > 1 else 0}"
        return None

    def _warn_if_http1_for_sse(self, request: Request) -> None:
        """Log a warning if SSE is being used over HTTP/1.x.

        This warning is only shown once per process to avoid log spam.
        HTTP/1.x connections suffer from head-of-line blocking, which can cause
        performance issues when SSE subscriptions share connections with other
        requests. HTTP/2 is strongly recommended for SSE.
        """
        global _sse_http1_warning_logged
        if _sse_http1_warning_logged:
            return

        http_version = self._get_http_version(request)
        if http_version and http_version.startswith("1."):
            _sse_http1_warning_logged = True
            logger = logging.getLogger("strawberry.http")
            logger.warning(
                "SSE subscription over HTTP/%s detected. "
                "HTTP/1.x connections suffer from head-of-line blocking, which can "
                "affect other requests sharing this connection. This warning will not "
                "be shown again. Consider using HTTP/2 or switching to "
                "graphql-transport-ws for subscriptions. "
                "See https://strawberry.rocks/docs/general/sse-subscriptions#http2-is-strongly-recommended-for-sse-subscriptions",
                http_version,
            )

    def _get_last_event_id(
        self, request_adapter: AsyncHTTPRequestAdapter
    ) -> int | None:
        """Extract Last-Event-ID header for SSE reconnection support.

        The Last-Event-ID header is sent by SSE clients when reconnecting,
        allowing the server to resume from the last processed event.
        Returns None if header is not present or invalid.
        """
        headers = {k.lower(): v for k, v in request_adapter.headers.items()}
        last_event_id = headers.get("last-event-id", "")
        if last_event_id:
            try:
                return int(last_event_id)
            except ValueError:
                return None
        return None

    async def _create_sse_error_response(
        self,
        request: Request,
        sub_response: SubResponse,
        code: str,
        message: str,
    ) -> Response:
        """Create an SSE error response when subscription limits are exceeded."""
        error_event = self.encode_sse_event(
            "error",
            [{"message": message, "code": code}],
        )
        complete_event = self.encode_sse_event("complete")

        async def error_stream() -> AsyncGenerator[str, None]:
            yield error_event
            yield complete_event

        return await self.create_streaming_response(
            request,
            error_stream,
            sub_response,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    def _make_heartbeat_stream(
        self,
        stream: Callable[[], AsyncGenerator[str, None]],
        heartbeat_message_provider: Callable[[], str],
        emit_error_event: bool = False,
        heartbeat_interval: float = 5.0,
        queue_maxsize: int | None = None,
    ) -> Callable[[], AsyncGenerator[str, None]]:
        """Shared heartbeat orchestration for SSE and multipart streams.

        Args:
            stream: The data stream to wrap with heartbeats.
            heartbeat_message_provider: Callable that returns the heartbeat message string.
            emit_error_event: If True, yield an error event before raising exceptions
                             (used by SSE). If False, just raise exceptions (multipart).
            heartbeat_interval: Interval in seconds between heartbeat messages.
            queue_maxsize: Maximum size of the internal queue for flow control.
                          Default is `sse_queue_buffer_size` attribute. Higher values
                          allow more buffering but increase memory usage.
        """
        import logging as logger_module

        log = logger_module.getLogger("strawberry.http")
        queue: asyncio.Queue[tuple[bool, bool, Any]] = asyncio.Queue(
            maxsize=queue_maxsize
            if queue_maxsize is not None
            else self.sse_queue_buffer_size,
        )
        cancelling = False

        async def drain() -> None:
            try:
                async for item in stream():
                    await queue.put((False, False, item))
            except Exception as e:
                if not cancelling:
                    await queue.put((True, False, e))
                else:
                    raise
            await queue.put((False, True, None))

        async def heartbeat() -> None:
            while True:
                item = heartbeat_message_provider()
                await queue.put((False, False, item))

                await asyncio.sleep(heartbeat_interval)

        async def merged() -> AsyncGenerator[str, None]:
            heartbeat_task = asyncio.create_task(heartbeat())
            task = asyncio.create_task(drain())

            async def cancel_tasks() -> None:
                nonlocal cancelling
                cancelling = True
                task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await task

                heartbeat_task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await heartbeat_task

            try:
                while not task.done():
                    raised, done, data = await queue.get()

                    if done:
                        break

                    if raised:
                        if emit_error_event:
                            log.error("SSE stream error: %s", data)
                            yield self.encode_sse_event(
                                "error", [{"message": str(data)}]
                            )
                        await cancel_tasks()
                        raise data

                    yield data
            finally:
                await cancel_tasks()

        return merged

    def _stream_sse_with_heartbeat(
        self, stream: Callable[[], AsyncGenerator[str, None]]
    ) -> Callable[[], AsyncGenerator[str, None]]:
        """Add SSE comment heartbeat messages to prevent connection timeouts.

        Uses SSE comments (lines starting with ':') as keepalive signals,
        which are silently ignored by SSE clients per the spec.
        """
        return self._make_heartbeat_stream(
            stream,
            heartbeat_message_provider=lambda: ":\n\n",
            emit_error_event=True,
            heartbeat_interval=self.sse_heartbeat_interval,
        )

    async def parse_multipart_subscriptions(
        self, request: AsyncHTTPRequestAdapter
    ) -> dict[str, str]:
        if request.method == "GET":
            return self.parse_query_params(request.query_params)

        return self.parse_json(await request.get_body())

    async def parse_http_body(
        self, request: AsyncHTTPRequestAdapter
    ) -> GraphQLRequestData | list[GraphQLRequestData]:
        headers = {key.lower(): value for key, value in request.headers.items()}
        content_type, _ = parse_content_type(request.content_type or "")
        accept = headers.get("accept", "")

        protocol: GraphQLSubscriptionProtocol
        if self._is_multipart_subscriptions(*parse_content_type(accept)):
            protocol = GraphQLSubscriptionProtocol.MULTIPART_SUBSCRIPTION
        elif self.sse_enabled and self._is_sse_subscription(accept):
            protocol = GraphQLSubscriptionProtocol.GRAPHQL_SSE
        else:
            protocol = GraphQLSubscriptionProtocol.HTTP

        if request.method == "GET":
            data = self.parse_query_params(request.query_params)
        elif "application/json" in content_type:
            data = self.parse_json(await request.get_body())
        elif self.multipart_uploads_enabled and content_type == "multipart/form-data":
            data = await self.parse_multipart(request)
        elif protocol in (
            GraphQLSubscriptionProtocol.GRAPHQL_SSE,
            GraphQLSubscriptionProtocol.MULTIPART_SUBSCRIPTION,
        ):
            # SSE and multipart subscription protocols require JSON request
            # bodies. Try parsing as JSON even when Content-Type is incorrect
            # to provide better error messages instead of "Unsupported content
            # type".
            data = self.parse_json(await request.get_body())
        else:
            raise HTTPException(400, "Unsupported content type")

        if isinstance(data, list):
            self._validate_batch_request(data, protocol=protocol)
            return [
                GraphQLRequestData(
                    query=item.get("query"),
                    variables=item.get("variables"),
                    operation_name=item.get("operationName"),
                    extensions=item.get("extensions"),
                    protocol=protocol,
                )
                for item in data
            ]

        query = data.get("query")
        if not isinstance(query, (str, type(None))):
            raise HTTPException(
                400,
                "The GraphQL operation's `query` must be a string or null, if provided.",
            )

        variables = data.get("variables")
        if not isinstance(variables, (dict, type(None))):
            raise HTTPException(
                400,
                "The GraphQL operation's `variables` must be an object or null, if provided.",
            )

        extensions = data.get("extensions")
        if not isinstance(extensions, (dict, type(None))):
            raise HTTPException(
                400,
                "The GraphQL operation's `extensions` must be an object or null, if provided.",
            )

        return GraphQLRequestData(
            query=query,
            variables=variables,
            operation_name=data.get("operationName"),
            extensions=extensions,
            protocol=protocol,
        )

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    async def on_ws_connect(
        self, context: Context
    ) -> UnsetType | None | dict[str, object]:
        return UNSET

    async def on_sse_connect(
        self, context: Context
    ) -> UnsetType | None | dict[str, object]:
        return UNSET


__all__ = ["AsyncBaseHTTPView"]
