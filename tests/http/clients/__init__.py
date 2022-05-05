import abc
import json
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional

from typing_extensions import Literal

from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult


JSON = Dict[str, Any]
ResultOverrideFunction = Optional[Callable[[ExecutionResult], GraphQLHTTPResponse]]


@dataclass
class Response:
    status_code: int
    data: bytes
    # TODO: headers

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
        graphiql: bool = True,
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
        **kwargs,
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
    ) -> Response:
        return await self._graphql_request(
            method, query=query, headers=headers, variables=variables, files=files
        )

    def _get_headers(
        self,
        method: Literal["get", "post"],
        headers: Optional[Dict[str, str]],
        files: Optional[Dict[str, BytesIO]],
    ) -> Dict[str, str]:
        addition_headers = (
            {
                "Content-Type": "application/json",
            }
            if method == "post" and not files
            else {}
        )

        if headers is None:
            return addition_headers

        return {**addition_headers, **headers}

    def _build_body(
        self,
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        method: Literal["get", "post"] = "post",
    ) -> Optional[Dict[str, object]]:
        if query is None:
            assert files is None
            assert variables is None

            return None

        body: Dict[str, object] = {"query": query}

        if variables:
            body["variables"] = variables

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
                folder_key = list(values.keys())[0]
                key += f".{folder_key}"
                # the list of file is inside the folder keyword
                values = values[folder_key]

            # If the variable is an array of files we must number the keys
            if isinstance(values, list):
                # copying `files` as when we map a file we must discard from the dict
                _kwargs = files.copy()
                for index, _ in enumerate(values):
                    k = list(_kwargs.keys())[0]
                    _kwargs.pop(k)
                    files_map.setdefault(k, [])
                    files_map[k].append(f"variables.{key}.{index}")
            else:
                files_map[key] = [f"variables.{key}"]

        return files_map
