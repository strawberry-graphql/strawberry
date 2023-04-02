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
    Tuple,
    Union,
)
from typing_extensions import Protocol

from strawberry import UNSET
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, GraphQLRequestData, process_result
from strawberry.schema.base import BaseSchema
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType

from .base import BaseView
from .exceptions import HTTPException
from .typevars import Context, Request, Response, RootValue


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

    async def get_form_data(self) -> Tuple[Mapping[str, Any], Mapping[str, Any]]:
        ...


class AsyncBaseHTTPView(
    abc.ABC, BaseView[Request], Generic[Request, Response, Context, RootValue]
):
    schema: BaseSchema
    graphiql: bool
    request_adapter_class: Callable[[Request], AsyncHTTPRequestAdapterProtocol]

    @property
    @abc.abstractmethod
    def allow_queries_via_get(self) -> bool:
        ...

    @abc.abstractmethod
    async def get_sub_response(self, request: Request) -> Response:
        ...

    @abc.abstractmethod
    async def get_context(self, request: Request, response: Response) -> Context:
        ...

    @abc.abstractmethod
    async def get_root_value(self, request: Request) -> Optional[RootValue]:
        ...

    @abc.abstractmethod
    def render_graphiql(self, request: Request) -> Response:
        # TODO: this could be non abstract
        # maybe add a get template function?
        ...

    @abc.abstractmethod
    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response
    ) -> Response:
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
        self, request: AsyncHTTPRequestAdapterProtocol
    ) -> Dict[str, str]:
        try:
            form_data, files = await request.get_form_data()
        except ValueError as e:
            raise HTTPException(400, "Unable to parse the multipart body") from e

        operations = form_data.get("operations", "{}")
        files_map = form_data.get("map", "{}")

        if isinstance(operations, (bytes, str)):
            operations = self.parse_json(operations)

        if isinstance(files_map, (bytes, str)):
            files_map = self.parse_json(files_map)

        try:
            return replace_placeholders_with_files(operations, files_map, files)
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

    async def run(
        self,
        request: Request,
        context: Optional[Context] = UNSET,
        root_value: Optional[RootValue] = UNSET,
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
        context = (
            await self.get_context(request, response=sub_response)
            if context is UNSET
            else context
        )
        root_value = (
            await self.get_root_value(request) if root_value is UNSET else root_value
        )

        assert context

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

        return self.create_response(
            response_data=response_data, sub_response=sub_response
        )

    async def parse_http_body(
        self, request: AsyncHTTPRequestAdapterProtocol
    ) -> GraphQLRequestData:
        content_type = request.content_type or ""

        if "application/json" in content_type:
            data = self.parse_json(await request.get_body())
        elif content_type.startswith("multipart/form-data"):
            data = await self.parse_multipart(request)
        elif request.method.lower() == "get":
            data = self.parse_query_params(request.query_params)
        else:
            raise HTTPException(400, "Unsupported content type")

        return GraphQLRequestData(
            query=data.get("query"),
            variables=data.get("variables"),  # type: ignore
            operation_name=data.get("operationName"),
        )

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)
