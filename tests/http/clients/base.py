import abc
import json
from dataclasses import dataclass
from io import BytesIO
from typing import (
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
)
from typing_extensions import Literal

from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.types import ExecutionResult

JSON = Dict[str, object]
ResultOverrideFunction = Optional[Callable[[ExecutionResult], GraphQLHTTPResponse]]


@dataclass
class Response:
    status_code: int
    data: bytes
    headers: Mapping[str, str]

    @property
    def text(self) -> str:
        return self.data.decode()

    @property
    def json(self) -> JSON:
        return json.loads(self.data)


class HttpClient(abc.ABC):
    @abc.abstractmethod
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        ...

    @abc.abstractmethod
    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        extensions: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        ...

    @abc.abstractmethod
    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        ...

    @abc.abstractmethod
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        ...

    @abc.abstractmethod
    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        ...

    async def query(
        self,
        query: Optional[str] = None,
        method: Literal["get", "post"] = "post",
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ) -> Response:
        return await self._graphql_request(
            method, query=query, headers=headers, variables=variables, files=files, extensions=extensions
        )

    def _get_headers(
        self,
        method: Literal["get", "post"],
        headers: Optional[Dict[str, str]],
        files: Optional[Dict[str, BytesIO]],
    ) -> Dict[str, str]:
        addition_headers = {}

        content_type = None

        if method == "post" and not files:
            content_type = "application/json"

        addition_headers = {"Content-Type": content_type} if content_type else {}

        return addition_headers if headers is None else {**addition_headers, **headers}

    def _build_body(
        self,
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        method: Literal["get", "post"] = "post",
        extensions: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, object]]:
        if query is None and extensions is None:
            assert files is None
            assert variables is None

            return None

        body: Dict[str, object] = {"query": query}

        if variables:
            body["variables"] = variables
        
        if extensions:
            body["extensions"] = extensions
    
        if files:
            assert variables is not None

            file_map = self._build_multipart_file_map(variables, files)

            body = {
                "operations": json.dumps(body),
                "map": json.dumps(file_map),
            }

        if method == "get" and variables:
            body["variables"] = json.dumps(variables)

        return body

    @staticmethod
    def _build_multipart_file_map(
        variables: Dict[str, object], files: Dict[str, BytesIO]
    ) -> Dict[str, List[str]]:
        # TODO: remove code duplication

        files_map: Dict[str, List[str]] = {}
        for key, values in variables.items():
            if isinstance(values, dict):
                folder_key = next(iter(values.keys()))
                key += f".{folder_key}"  # noqa: PLW2901
                # the list of file is inside the folder keyword
                values = values[folder_key]  # noqa: PLW2901

            # If the variable is an array of files we must number the keys
            if isinstance(values, list):
                # copying `files` as when we map a file we must discard from the dict
                _kwargs = files.copy()
                for index, _ in enumerate(values):
                    k = next(iter(_kwargs.keys()))
                    _kwargs.pop(k)
                    files_map.setdefault(k, [])
                    files_map[k].append(f"variables.{key}.{index}")
            else:
                files_map[key] = [f"variables.{key}"]

        return files_map

    def create_app(self, **kwargs: Any) -> None:
        """
        For use by websocket tests
        """
        raise NotImplementedError

    async def ws_connect(
        self,
        url: str,
        *,
        protocols: List[str],
    ) -> AsyncContextManager["WebSocketClient"]:
        raise NotImplementedError


@dataclass
class Message:
    type: Any
    data: Any
    extra: Optional[str] = None

    def json(self) -> Any:
        return json.loads(self.data)


class WebSocketClient(abc.ABC):
    def name(self) -> str:
        return ""

    @abc.abstractmethod
    async def send_json(self, payload: Dict[str, Any]) -> None:
        ...

    @abc.abstractmethod
    async def send_bytes(self, payload: bytes) -> None:
        ...

    @abc.abstractmethod
    async def receive(self, timeout: Optional[float] = None) -> Message:
        ...

    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        ...

    @abc.abstractmethod
    async def close(self) -> None:
        ...

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def close_code(self) -> int:
        ...

    @abc.abstractmethod
    def assert_reason(self, reason: str) -> None:
        ...

    async def __aiter__(self) -> AsyncGenerator[Message, None]:
        while not self.closed:
            yield await self.receive()


class DebuggableGraphQLTransportWSMixin:
    @staticmethod
    def on_init(self):
        """
        This method can be patched by unittests to get the instance of the
        transport handler when it is initialized
        """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        DebuggableGraphQLTransportWSMixin.on_init(self)

    def get_tasks(self) -> List:
        return [op.task for op in self.operations.values()]

    async def get_context(self) -> object:
        context = await super().get_context()
        context["ws"] = self._ws
        context["get_tasks"] = self.get_tasks
        context["connectionInitTimeoutTask"] = self.connection_init_timeout_task
        return context


class DebuggableGraphQLWSMixin:
    def get_tasks(self) -> List:
        return list(self.tasks.values())

    async def get_context(self) -> object:
        context = await super().get_context()
        context["ws"] = self._ws
        context["get_tasks"] = self.get_tasks
        context["connectionInitTimeoutTask"] = None
        return context
