import abc
import json
from typing import (
    Callable,
    Generic,
    Literal,
    Optional,
    Union,
)

from graphql import GraphQLError
from lia import HTTPException, SyncHTTPRequestAdapter

from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import (
    GraphQLHTTPResponse,
    GraphQLRequestData,
    process_result,
)
from strawberry.http.ides import GraphQL_IDE
from strawberry.schema import BaseSchema
from strawberry.schema.exceptions import (
    CannotGetOperationTypeError,
    InvalidOperationTypeError,
)
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType
from strawberry.types.unset import UNSET

from .base import BaseView
from .parse_content_type import parse_content_type
from .typevars import Context, Request, Response, RootValue, SubResponse


class SyncBaseHTTPView(
    abc.ABC,
    BaseView[Request],
    Generic[Request, Response, SubResponse, Context, RootValue],
):
    schema: BaseSchema
    graphiql: Optional[bool]
    graphql_ide: Optional[GraphQL_IDE]
    request_adapter_class: Callable[[Request], SyncHTTPRequestAdapter]

    # Methods that need to be implemented by individual frameworks

    @property
    @abc.abstractmethod
    def allow_queries_via_get(self) -> bool: ...

    @abc.abstractmethod
    def get_sub_response(self, request: Request) -> SubResponse: ...

    @abc.abstractmethod
    def get_context(self, request: Request, response: SubResponse) -> Context: ...

    @abc.abstractmethod
    def get_root_value(self, request: Request) -> Optional[RootValue]: ...

    @abc.abstractmethod
    def create_response(
        self,
        response_data: Union[GraphQLHTTPResponse, list[GraphQLHTTPResponse]],
        sub_response: SubResponse,
    ) -> Response: ...

    @abc.abstractmethod
    def render_graphql_ide(self, request: Request) -> Response: ...

    def execute_operation(
        self,
        request: Request,
        context: Context,
        root_value: Optional[RootValue],
        sub_response: SubResponse,
    ) -> Union[ExecutionResult, list[ExecutionResult]]:
        request_adapter = self.request_adapter_class(request)

        try:
            request_data = self.parse_http_body(request_adapter)
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
            return [
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

        return self.execute_single(
            request=request,
            request_adapter=request_adapter,
            sub_response=sub_response,
            context=context,
            root_value=root_value,
            request_data=request_data,
        )

    def execute_single(
        self,
        request: Request,
        request_adapter: SyncHTTPRequestAdapter,
        sub_response: SubResponse,
        context: Context,
        root_value: Optional[RootValue],
        request_data: GraphQLRequestData,
    ) -> ExecutionResult:
        allowed_operation_types = OperationType.from_http(request_adapter.method)

        if not self.allow_queries_via_get and request_adapter.method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        try:
            result = self.schema.execute_sync(
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

    def parse_multipart(self, request: SyncHTTPRequestAdapter) -> dict[str, str]:
        operations = self.parse_json(request.post_data.get("operations", "{}"))
        files_map = self.parse_json(request.post_data.get("map", "{}"))

        try:
            return replace_placeholders_with_files(operations, files_map, request.files)
        except KeyError as e:
            raise HTTPException(400, "File(s) missing in form data") from e

    def parse_http_body(
        self, request: SyncHTTPRequestAdapter
    ) -> Union[GraphQLRequestData, list[GraphQLRequestData]]:
        headers = {key.lower(): value for key, value in request.headers.items()}
        content_type, params = parse_content_type(request.content_type or "")
        accept = headers.get("accept", "")

        protocol: Literal["http", "multipart-subscription"] = (
            "multipart-subscription"
            if self._is_multipart_subscriptions(*parse_content_type(accept))
            else "http"
        )

        if request.method == "GET":
            data = self.parse_query_params(request.query_params)
        elif "application/json" in content_type:
            data = self.parse_json(request.body)
        # TODO: multipart via get?
        elif self.multipart_uploads_enabled and content_type == "multipart/form-data":
            data = self.parse_multipart(request)
        elif self._is_multipart_subscriptions(content_type, params):
            raise HTTPException(
                400, "Multipart subcriptions are not supported in sync mode"
            )
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
        )

    def _handle_errors(
        self, errors: list[GraphQLError], response_data: GraphQLHTTPResponse
    ) -> None:
        """Hook to allow custom handling of errors, used by the Sentry Integration."""

    def run(
        self,
        request: Request,
        context: Context = UNSET,
        root_value: Optional[RootValue] = UNSET,
    ) -> Response:
        request_adapter = self.request_adapter_class(request)

        if not self.is_request_allowed(request_adapter):
            raise HTTPException(405, "GraphQL only supports GET and POST requests.")

        if self.should_render_graphql_ide(request_adapter):
            if self.graphql_ide:
                return self.render_graphql_ide(request)
            raise HTTPException(404, "Not Found")

        sub_response = self.get_sub_response(request)
        context = (
            self.get_context(request, response=sub_response)
            if context is UNSET
            else context
        )
        root_value = self.get_root_value(request) if root_value is UNSET else root_value

        result = self.execute_operation(
            request=request,
            context=context,
            root_value=root_value,
            sub_response=sub_response,
        )

        response_data: Union[GraphQLHTTPResponse, list[GraphQLHTTPResponse]]

        if isinstance(result, list):
            response_data = []
            for execution_result in result:
                processed_result = self.process_result(
                    request=request, result=execution_result
                )
                if execution_result.errors:
                    self._handle_errors(execution_result.errors, processed_result)
                response_data.append(processed_result)
        else:
            response_data = self.process_result(request=request, result=result)

            if result.errors:
                self._handle_errors(result.errors, response_data)

        return self.create_response(
            response_data=response_data, sub_response=sub_response
        )

    def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)


__all__ = ["SyncBaseHTTPView"]
