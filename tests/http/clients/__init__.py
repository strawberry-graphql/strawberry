import abc
import json
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, List, Optional

from typing_extensions import Literal


JSON = Dict[str, Any]


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
    def __init__(self, graphiql: bool = True):
        ...

    @abc.abstractmethod
    async def _request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        ...

    async def get(
        self,
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        return await self._request("get", query=query, headers=headers)

    async def post(
        self,
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        return await self._request(
            "post", query=query, variables=variables, files=files, headers=headers
        )

    def _build_body(
        self,
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
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
