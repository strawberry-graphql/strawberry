import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from typing_extensions import Literal, TypedDict


@dataclass
class Response:
    errors: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]
    extensions: Optional[Dict[str, Any]]


class Body(TypedDict, total=False):
    query: str
    variables: Optional[Dict[str, Any]]


class BaseGraphQLTestClient(ABC):
    def __init__(self, client):
        self._client = client

    @abstractmethod
    def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        asserts_errors: Optional[bool] = True,
        format: Literal["multipart", "json"] = "json",
        files: Optional[Dict[str, Any]] = None,
    ) -> Response:
        raise NotImplementedError


class GraphQLTestClient(BaseGraphQLTestClient):
    def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        asserts_errors: Optional[bool] = True,
        format: Literal["multipart", "json"] = "json",
        files: Optional[Dict[str, Any]] = None,
    ) -> Response:
        body: Any = {"query": query}

        if variables:
            body["variables"] = variables

        if format == "multipart":
            assert variables is not None
            assert files is not None
            file_map = GraphQLTestClient._build_multipart_file_map(variables, files)

            body = {
                "operations": json.dumps(body),
                "map": json.dumps(file_map),
                **files,
            }

            response = self._client.post(
                "/graphql/", data=body, format="multipart", headers=headers
            )
            data = json.loads(response.content.decode())

        elif format == "json":
            resp = self._client.post(
                "/graphql/", data=body, content_type="application/json", headers=headers
            )
            data = resp.json()

        response = Response(
            errors=data.get("errors"),
            data=data.get("data"),
            extensions=data.get("extensions"),
        )
        if asserts_errors:
            assert response.errors is None

        return response

    @staticmethod
    def _build_multipart_file_map(
        variables: Dict[str, Any], files: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Creates the file mapping between the variables and the files objects passed
        as key arguments

        Example usages:

        >>> _build_multipart_file_map(
        >>>     variables={"textFile": None}, files={"textFile": f}
        >>> )
        ... {"textFile": ["variables.textFile"]}

        If the variable is a list we have to enumerate files in the mapping
        >>> _build_multipart_file_map(
        >>>     variables={"files": [None, None]},
        >>>     files={"file1": file1, "file2": file2},
        >>> )
        ... {"file1": ["variables.files.0"], "file2": ["variables.files.1"]}

        If `variables` contains another keyword (a folder) we must include that keyword
        in the mapping
        >>> _build_multipart_file_map(
        >>>     variables={"folder": {"files": [None, None]}},
        >>>     files={"file1": file1, "file2": file2},
        >>> )
        ... {
        ...     "file1": ["variables.files.folder.files.0"],
        ...     "file2": ["variables.files.folder.files.1"]
        ... }

        If `variables` includes both a list of files and other single values, we must
        map them accordingly
        >>> _build_multipart_file_map(
        >>>     variables={"files": [None, None], "textFile": None},
        >>>     files={"file1": file1, "file2": file2, "textFile": file3},
        >>> )
        ... {
        ...     "file1": ["variables.files.0"],
        ...     "file2": ["variables.files.1"],
        ...     "textFile": ["variables.textFile"],
        ... }
        """

        map: Dict[str, Any] = {}
        for key, values in variables.items():
            reference = key
            variable_values = values

            # In case of folders the variables will look like
            # `{"folder": {"files": ...]}}`
            if isinstance(values, dict):
                folder_key = list(values.keys())[0]
                reference += f".{folder_key}"
                # the list of file is inside the folder keyword
                variable_values = variable_values[folder_key]

            # If the variable is an array of files we must number the keys
            if isinstance(variable_values, list):
                # copying `files` as when we map a file we must discard from the dict
                _kwargs = files.copy()
                for index, _ in enumerate(variable_values):
                    k = list(_kwargs.keys())[0]
                    _kwargs.pop(k)
                    map.setdefault(k, [])
                    map[k].append(f"variables.{reference}.{index}")
            else:
                map[key] = [f"variables.{reference}"]

        return map
