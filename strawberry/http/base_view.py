import abc
import json
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
)
from typing_extensions import Protocol

from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, GraphQLRequestData, process_result
from strawberry.schema import BaseSchema
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType


class RequestProtocol(Protocol):
    method: str
    content_type: Optional[str]
    # TODO: this is probably going to be different
    # body, content, data, etc, binary or not
    data: Union[str, bytes]
    form: Mapping[str, Union[str, bytes]]
    files: Mapping[str, Any]


Request = TypeVar("Request")
Response = TypeVar("Response")
Context = TypeVar("Context")
RootValue = TypeVar("RootValue")


class HTTPException(Exception):
    def __init__(self, status_code: int, reason: str):
        self.status_code = status_code
        self.reason = reason


class HTTPRequestAdapterProtocol(Protocol):
    @property
    def query_params(self) -> Dict[str, Union[str, List[str]]]:
        ...

    @property
    def body(self) -> str:
        ...

    @property
    def method(self) -> str:
        ...

    @property
    def headers(self) -> Mapping[str, str]:
        ...

    @property
    def post_data(self) -> Mapping[str, Union[str, bytes]]:
        ...

    @property
    def files(self) -> Mapping[str, Any]:
        ...

    @property
    def content_type(self) -> Optional[str]:
        ...


class AsyncHTTPRequestAdapterProtocol(Protocol):
    @property
    def query_params(self) -> Dict[str, Union[str, List[str]]]:
        ...

    @property
    def method(self) -> str:
        ...

    @property
    def headers(self) -> Mapping[str, str]:
        ...

    @property
    def content_type(self) -> Optional[str]:
        ...

    async def get_body(self) -> str:
        ...

    async def get_post_data(self) -> Mapping[str, Union[str, bytes]]:
        ...

    # TODO: this gets everything, not just files
    async def get_files(self) -> Mapping[str, Any]:
        ...


class BaseHTTPView(abc.ABC, Generic[Request, Response, Context, RootValue]):
    schema: BaseSchema
    graphiql: bool
    request_adapter_class: Callable[[Request], HTTPRequestAdapterProtocol]

    # Methods that need to be implemented by individual frameworks

    @property
    @abc.abstractmethod
    def allow_queries_via_get(self) -> bool:
        ...

    @abc.abstractmethod
    def get_sub_response(self, request: Request) -> Response:
        ...

    @abc.abstractmethod
    def get_context(self, request: Request, response: Response) -> Context:
        ...

    @abc.abstractmethod
    def get_root_value(self, request: Request) -> Optional[RootValue]:
        ...

    @abc.abstractmethod
    def render_graphiql(self, request: Request) -> Response:
        # TODO: this could be non abstract
        # maybe add a get template function?
        ...

    # Internal methods

    def is_request_allowed(self, request: HTTPRequestAdapterProtocol) -> bool:
        return request.method.lower() in ("get", "post")

    def should_render_graphiql(self, request: HTTPRequestAdapterProtocol) -> bool:
        return (
            request.method.lower() == "get"
            and request.query_params.get("query") is None
            and any(
                supported_header in request.headers.get("accept", "")
                for supported_header in ("text/html", "*/*")
            )
        )

    def execute_operation(
        self, request: Request, context: Context, root_value: Optional[RootValue]
    ) -> ExecutionResult:
        request_adapter = self.request_adapter_class(request)

        try:
            request_data = self.parse_http_body(request_adapter)
        except json.decoder.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e
            # DO this only when doing files
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

        method = request_adapter.method.lower()

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "get":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        assert self.schema

        return self.schema.execute_sync(
            request_data.query,
            root_value=root_value,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
            allowed_operation_types=allowed_operation_types,
        )

    def parse_json(self, data: Union[str, bytes]) -> Dict[str, str]:
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e

    def encode_json(self, response_data: GraphQLHTTPResponse) -> str:
        return json.dumps(response_data)

    def parse_multipart(self, request: HTTPRequestAdapterProtocol) -> Dict[str, str]:
        operations = self.parse_json(request.post_data.get("operations", "{}"))
        files_map = self.parse_json(request.post_data.get("map", "{}"))

        # TODO: remove type ignore below

        try:
            return replace_placeholders_with_files(operations, files_map, request.files)
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

    def parse_http_body(
        self, request: HTTPRequestAdapterProtocol
    ) -> GraphQLRequestData:
        content_type = request.content_type or ""

        if "application/json" in content_type:
            data = self.parse_json(request.body)
        elif content_type.startswith("multipart/form-data"):
            data = self.parse_multipart(request)
        elif request.method.lower() == "get":
            data = self.parse_query_params(request.query_params)
        else:
            # TODO, is this raise fine?
            raise HTTPException(400, "Unsupported content type")

        return GraphQLRequestData(
            query=data.get("query"),
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
        )

    def parse_query_params(self, params: Dict[str, str]) -> Dict[str, Any]:
        if "variables" in params:
            params["variables"] = json.loads(params["variables"])

        return params

    def run(
        self,
        request: Request,
        context: Optional[Context] = None,
        root_value: Optional[RootValue] = None,
    ) -> Response:
        request_adapter = self.request_adapter_class(request)

        if not self.is_request_allowed(request_adapter):
            raise HTTPException(405, "GraphQL only supports GET and POST requests.")

        if self.should_render_graphiql(request_adapter):
            if self.graphiql:
                return self.render_graphiql(request)
            else:
                raise HTTPException(404, "Not Found")

        sub_response = self.get_sub_response(request)
        context = context or self.get_context(request, response=sub_response)
        root_value = root_value or self.get_root_value(request)

        try:
            result = self.execute_operation(
                request=request,
                context=context,
                root_value=root_value,
            )
        except InvalidOperationTypeError as e:
            raise HTTPException(
                400, e.as_http_error_reason(request_adapter.method)
            ) from e
        except MissingQueryError as e:
            raise HTTPException(400, "No GraphQL query found in the request") from e

        response_data = self.process_result(request=request, result=result)

        return self._create_response(
            response_data=response_data, sub_response=sub_response
        )

    def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)


class AsyncBaseHTTPView(BaseHTTPView[Request, Response, Context, RootValue]):
    request_adapter_class: Type[AsyncHTTPRequestAdapterProtocol]

    @abc.abstractmethod
    async def get_sub_response(self, request: Request) -> Response:
        ...

    @abc.abstractmethod
    async def get_context(self, request: Request, response: Response) -> Context:
        ...

    @abc.abstractmethod
    async def get_root_value(self, request: Request) -> Optional[RootValue]:
        ...

    async def execute_operation(
        self, request: Request, context: Context, root_value: Optional[RootValue]
    ) -> ExecutionResult:
        request_adapter = self.request_adapter_class(request)

        try:
            request_data = await self.parse_http_body(request_adapter)
        except json.decoder.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e
            # DO this only when doing files
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

        method = request_adapter.method.lower()

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "get":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        assert self.schema

        return await self.schema.execute(
            request_data.query,
            root_value=root_value,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
            allowed_operation_types=allowed_operation_types,
        )

    async def parse_multipart(
        self, request: HTTPRequestAdapterProtocol
    ) -> Dict[str, str]:
        try:
            files, operations, files_map = await request.get_files()
        except ValueError:
            raise HTTPException(400, "Unable to parse the multipart body")

        try:
            return replace_placeholders_with_files(operations, files_map, files)
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

    async def run(
        self,
        request: Request,
        context: Optional[Context] = None,
        root_value: Optional[RootValue] = None,
    ) -> Response:
        request_adapter = self.request_adapter_class(request)

        if not self.is_request_allowed(request_adapter):
            raise HTTPException(405, "GraphQL only supports GET and POST requests.")

        if self.should_render_graphiql(request_adapter):
            if self.graphiql:
                return self.render_graphiql(request)
            else:
                raise HTTPException(404, "Not Found")

        sub_response = await self.get_sub_response(request)
        context = context or await self.get_context(request, response=sub_response)
        root_value = root_value or await self.get_root_value(request)

        try:
            result = await self.execute_operation(
                request=request, context=context, root_value=root_value
            )
        except InvalidOperationTypeError as e:
            raise HTTPException(
                400, e.as_http_error_reason(request_adapter.method)
            ) from e
        except MissingQueryError as e:
            raise HTTPException(400, "No GraphQL query found in the request") from e

        response_data = await self.process_result(request=request, result=result)

        return self._create_response(
            response_data=response_data, sub_response=sub_response
        )

    async def parse_http_body(
        self, request: HTTPRequestAdapterProtocol
    ) -> GraphQLRequestData:
        content_type = request.content_type or ""

        if "application/json" in content_type:
            data = self.parse_json(await request.get_body())
        elif content_type.startswith("multipart/form-data"):
            data = await self.parse_multipart(request)
        elif request.method.lower() == "get":
            data = self.parse_query_params(request.query_params)
        else:
            # TODO, is this raise fine?
            raise HTTPException(400, "Unsupported content type")

        return GraphQLRequestData(
            query=data.get("query"),
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
        )

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return super().process_result(request, result)
