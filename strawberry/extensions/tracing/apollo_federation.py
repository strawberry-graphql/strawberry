"""Apollo Federation Tracing (FTV1) Extension.

This extension provides support for Apollo Federation's inline tracing format (ftv1).
When a request includes the 'apollo-federation-include-trace: ftv1' header,
this extension will include trace data in the response under extensions.ftv1.

Usage
-----

Use the async version for asynchronous schemas::

    from strawberry import Schema
    from strawberry.extensions.tracing.apollo_federation import (
        ApolloFederationTracingExtension,
    )

    schema = Schema(
        query=Query,
        extensions=[ApolloFederationTracingExtension],
    )

Use the synchronous version for synchronous schemas::

    from strawberry import Schema
    from strawberry.extensions.tracing.apollo_federation import (
        ApolloFederationTracingExtensionSync,
    )

    schema = Schema(
        query=Query,
        extensions=[ApolloFederationTracingExtensionSync],
    )

Framework Support
-----------------

This extension is designed to work with any Strawberry integration that provides
HTTP request headers through the execution context. The extension checks for the
FTV1 header by looking for request.headers in the context.

Supported integrations include:
- FastAPI / Starlette (ASGI)
- Flask
- Django
- Quart
- Sanic
- AIOHTTP
- Any integration that exposes request.headers

The context can be either:
- A dict with a 'request' key: ``{"request": request}``
- An object with a 'request' attribute: ``context.request``

Requirements
------------

Requires the 'protobuf' package to be installed. If not available, the extension
will disable itself silently and not include tracing data in responses.

Install with: ``pip install protobuf``
"""

from __future__ import annotations

import contextlib
import time
from base64 import b64encode
from inspect import isawaitable
from typing import TYPE_CHECKING, Any

from strawberry.extensions import SchemaExtension

from .utils import should_skip_tracing

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from graphql import GraphQLResolveInfo

    from strawberry.types.execution import ExecutionContext

# Header that triggers ftv1 tracing
FTV1_HEADER = "apollo-federation-include-trace"
FTV1_HEADER_VALUE = "ftv1"


def _get_protobuf_timestamp() -> Any:
    """Create a protobuf Timestamp with current time."""
    from google.protobuf.timestamp_pb2 import Timestamp

    ts = Timestamp()
    ts.GetCurrentTime()
    return ts


def _check_protobuf_available() -> None:
    """Check if protobuf is available, raise ImportError if not."""
    try:
        import google.protobuf  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "The 'protobuf' package is required for Apollo Federation tracing. "
            "Install it with: pip install protobuf"
        ) from e


def _encode_varint(value: int) -> bytes:
    """Encode an integer as a protobuf varint."""
    parts = []
    while value > 127:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts)


class _SimpleTrace:
    """Minimal Trace message for FTV1."""

    def __init__(self) -> None:
        self.start_time: Any = None
        self.end_time: Any = None
        self.duration_ns: int = 0
        self.root: _SimpleNode | None = None

    def SerializeToString(self) -> bytes:  # noqa: N802
        """Serialize to protobuf binary format."""
        parts = []

        # Field 4: start_time (Timestamp)
        if self.start_time:
            ts_bytes = self.start_time.SerializeToString()
            parts.append(b"\x22")  # field 4, wire type 2 (length-delimited)
            parts.append(_encode_varint(len(ts_bytes)))
            parts.append(ts_bytes)

        # Field 3: end_time (Timestamp)
        if self.end_time:
            ts_bytes = self.end_time.SerializeToString()
            parts.append(b"\x1a")  # field 3, wire type 2
            parts.append(_encode_varint(len(ts_bytes)))
            parts.append(ts_bytes)

        # Field 11: duration_ns (uint64)
        if self.duration_ns:
            parts.append(b"\x58")  # field 11, wire type 0 (varint)
            parts.append(_encode_varint(self.duration_ns))

        # Field 14: root (Node)
        if self.root:
            node_bytes = self.root.SerializeToString()
            parts.append(b"\x72")  # field 14, wire type 2
            parts.append(_encode_varint(len(node_bytes)))
            parts.append(node_bytes)

        return b"".join(parts)


class _SimpleNode:
    """Minimal Node message for FTV1."""

    def __init__(self) -> None:
        self.response_name: str | None = None
        self.index: int | None = None
        self.type: str | None = None
        self.parent_type: str | None = None
        self.start_time: int = 0
        self.end_time: int = 0
        self.children: list[_SimpleNode] = []

    def SerializeToString(self) -> bytes:  # noqa: N802
        """Serialize to protobuf binary format."""
        parts = []

        # Field 1: response_name (string) - oneof id
        if self.response_name is not None:
            name_bytes = self.response_name.encode("utf-8")
            parts.append(b"\x0a")  # field 1, wire type 2
            parts.append(_encode_varint(len(name_bytes)))
            parts.append(name_bytes)
        # Field 2: index (uint32) - oneof id
        elif self.index is not None:
            parts.append(b"\x10")  # field 2, wire type 0
            parts.append(_encode_varint(self.index))

        # Field 3: type (string)
        if self.type:
            type_bytes = self.type.encode("utf-8")
            parts.append(b"\x1a")  # field 3, wire type 2
            parts.append(_encode_varint(len(type_bytes)))
            parts.append(type_bytes)

        # Field 13: parent_type (string)
        if self.parent_type:
            pt_bytes = self.parent_type.encode("utf-8")
            parts.append(b"\x6a")  # field 13, wire type 2
            parts.append(_encode_varint(len(pt_bytes)))
            parts.append(pt_bytes)

        # Field 8: start_time (uint64)
        if self.start_time:
            parts.append(b"\x40")  # field 8, wire type 0
            parts.append(_encode_varint(self.start_time))

        # Field 9: end_time (uint64)
        if self.end_time:
            parts.append(b"\x48")  # field 9, wire type 0
            parts.append(_encode_varint(self.end_time))

        # Field 12: child (repeated Node)
        for child in self.children:
            child_bytes = child.SerializeToString()
            parts.append(b"\x62")  # field 12, wire type 2
            parts.append(_encode_varint(len(child_bytes)))
            parts.append(child_bytes)

        return b"".join(parts)


def _create_trace() -> tuple[type[_SimpleTrace], type[_SimpleNode]]:
    """Return the Trace and Node classes after checking protobuf availability.

    Classes are defined at module scope for efficiency.
    This function just validates protobuf is available.
    """
    _check_protobuf_available()
    return _SimpleTrace, _SimpleNode


class ApolloFederationTracingExtension(SchemaExtension):
    """Extension that provides Apollo Federation inline tracing (ftv1).

    This extension checks for the 'apollo-federation-include-trace: ftv1' header
    and, when present, records timing information for each resolver and includes
    it in the response as a base64-encoded protobuf under extensions.ftv1.
    """

    def __init__(self, execution_context: ExecutionContext) -> None:
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context
        self._should_trace = False
        self._trace: _SimpleTrace | None = None
        self._root_node: _SimpleNode | None = None
        self._nodes: dict[str, _SimpleNode] = {}
        self._start_time_ns: int = 0

    def _check_should_trace(self) -> bool:
        """Check if the request includes the ftv1 header."""
        context = self.execution_context.context
        if context is None:
            return False

        # Handle dict-style context (common in ASGI/Starlette)
        request = None
        if isinstance(context, dict):
            request = context.get("request")
        elif hasattr(context, "request"):
            request = context.request

        if request is None:
            return False

        # Get headers from request - support multiple frameworks
        headers: dict[str, str] = {}
        if hasattr(request, "headers"):
            # Most frameworks (Starlette, FastAPI, Flask, Django, Quart, Sanic, AIOHTTP)
            # provide a headers object that can be iterated
            with contextlib.suppress(AttributeError, TypeError):
                headers = {k.lower(): v for k, v in request.headers.items()}

        return headers.get(FTV1_HEADER, "").lower() == FTV1_HEADER_VALUE

    def on_operation(self) -> Generator[None, None, None]:
        self._should_trace = self._check_should_trace()

        if self._should_trace:
            try:
                _create_trace()  # Validates protobuf is available
                self._trace = _SimpleTrace()
                self._trace.start_time = _get_protobuf_timestamp()
                self._start_time_ns = time.perf_counter_ns()

                # Create root node
                self._root_node = _SimpleNode()
                self._nodes[""] = self._root_node
            except ImportError:
                # protobuf not installed, disable tracing
                self._should_trace = False

        yield

        if self._should_trace and self._trace:
            self._trace.end_time = _get_protobuf_timestamp()
            self._trace.duration_ns = time.perf_counter_ns() - self._start_time_ns
            self._trace.root = self._root_node

    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if not self._should_trace or should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)
            if isawaitable(result):
                result = await result
            return result

        # Record resolver timing
        start_time = time.perf_counter_ns() - self._start_time_ns
        node = self._create_node(info)
        node.start_time = start_time

        try:
            result = _next(root, info, *args, **kwargs)
            if isawaitable(result):
                result = await result
            return result
        finally:
            node.end_time = time.perf_counter_ns() - self._start_time_ns

    def _create_node(self, info: GraphQLResolveInfo) -> _SimpleNode:
        """Create a trace node for a resolver."""
        path = info.path
        path_str = self._path_to_string(path)
        parent_path_str = self._path_to_string(path.prev) if path.prev else ""

        # Get or create parent node
        parent_node = self._nodes.get(parent_path_str)
        if parent_node is None and path.prev:
            # Need to create intermediate nodes
            parent_node = self._ensure_parent_node(path.prev)

        if parent_node is None:
            parent_node = self._root_node

        # Create this node
        node = _SimpleNode()
        if isinstance(path.key, int):
            node.index = path.key
        else:
            node.response_name = path.key

        node.type = str(info.return_type)
        node.parent_type = str(info.parent_type)

        # Add to parent's children
        if parent_node is not None:
            parent_node.children.append(node)
        self._nodes[path_str] = node

        return node

    def _ensure_parent_node(self, path: Any) -> _SimpleNode:
        """Ensure all parent nodes exist in the tree."""
        path_str = self._path_to_string(path)
        if path_str in self._nodes:
            return self._nodes[path_str]

        parent_path_str = self._path_to_string(path.prev) if path.prev else ""
        parent_node = self._nodes.get(parent_path_str)
        if parent_node is None and path.prev:
            parent_node = self._ensure_parent_node(path.prev)
        if parent_node is None:
            parent_node = self._root_node

        node = _SimpleNode()
        if isinstance(path.key, int):
            node.index = path.key
        else:
            node.response_name = path.key

        if parent_node is not None:
            parent_node.children.append(node)
        self._nodes[path_str] = node
        return node

    def _path_to_string(self, path: Any) -> str:
        """Convert a GraphQL path to a string key."""
        if path is None:
            return ""

        parts = []
        current = path
        while current is not None:
            parts.append(str(current.key))
            current = current.prev

        return ".".join(reversed(parts))

    def get_results(self) -> dict[str, Any]:
        if not self._should_trace or not self._trace:
            return {}

        trace_bytes = self._trace.SerializeToString()
        ftv1 = b64encode(trace_bytes).decode("utf-8")
        return {"ftv1": ftv1}


class ApolloFederationTracingExtensionSync(ApolloFederationTracingExtension):
    """Synchronous version of the Apollo Federation tracing extension."""

    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if not self._should_trace or should_skip_tracing(_next, info):
            return _next(root, info, *args, **kwargs)

        # Record resolver timing
        start_time = time.perf_counter_ns() - self._start_time_ns
        node = self._create_node(info)
        node.start_time = start_time

        try:
            return _next(root, info, *args, **kwargs)
        finally:
            node.end_time = time.perf_counter_ns() - self._start_time_ns


__all__ = [
    "ApolloFederationTracingExtension",
    "ApolloFederationTracingExtensionSync",
]
