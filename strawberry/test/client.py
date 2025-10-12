from __future__ import annotations

import json
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from collections.abc import Coroutine, Mapping

    from graphql import GraphQLFormattedError


@dataclass
class Response:
    errors: list[GraphQLFormattedError] | None
    data: dict[str, object] | None
    extensions: dict[str, object] | None


class Body(TypedDict, total=False):
    query: str
    variables: dict[str, object] | None


class BaseGraphQLTestClient(ABC):
    def __init__(
        self,
        client: Any,
        url: str = "/graphql/",
    ) -> None:
        self._client = client
        self.url = url

    def query(
        self,
        query: str,
        variables: dict[str, Mapping] | None = None,
        headers: dict[str, object] | None = None,
        asserts_errors: bool | None = None,
        files: dict[str, object] | None = None,
        assert_no_errors: bool | None = True,
    ) -> Coroutine[Any, Any, Response] | Response:
        body = self._build_body(query, variables, files)

        resp = self.request(body, headers, files)
        data = self._decode(resp, type="multipart" if files else "json")

        response = Response(
            errors=data.get("errors"),
            data=data.get("data"),
            extensions=data.get("extensions"),
        )

        if asserts_errors is not None:
            warnings.warn(
                "The `asserts_errors` argument has been renamed to `assert_no_errors`",
                DeprecationWarning,
                stacklevel=2,
            )

        assert_no_errors = (
            assert_no_errors if asserts_errors is None else asserts_errors
        )

        if assert_no_errors:
            assert response.errors is None

        return response

    @abstractmethod
    def request(
        self,
        body: dict[str, object],
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
    ) -> Any:
        raise NotImplementedError

    def _build_body(
        self,
        query: str,
        variables: dict[str, Mapping] | None = None,
        files: dict[str, object] | None = None,
    ) -> dict[str, object]:
        body: dict[str, object] = {"query": query}

        if variables:
            body["variables"] = variables

        if files:
            assert variables is not None
            assert files is not None
            file_map = BaseGraphQLTestClient._build_multipart_file_map(variables, files)

            body = {
                "operations": json.dumps(body),
                "map": json.dumps(file_map),
                **files,
            }

        return body

    @staticmethod
    def _build_multipart_file_map(
        variables: dict[str, Mapping], files: dict[str, object]
    ) -> dict[str, list[str]]:
        """Creates the file mapping between the variables and the files objects passed as key arguments.

        Args:
            variables: A dictionary with the variables that are going to be passed to the
                query.
            files: A dictionary with the files that are going to be passed to the query.

        Example usages:

        ```python
        _build_multipart_file_map(variables={"textFile": None}, files={"textFile": f})
        # {"textFile": ["variables.textFile"]}
        ```

        If the variable is a list we have to enumerate files in the mapping

        ```python
        _build_multipart_file_map(
            variables={"files": [None, None]},
            files={"file1": file1, "file2": file2},
        )
        # {"file1": ["variables.files.0"], "file2": ["variables.files.1"]}
        ```

        If `variables` contains another keyword (a folder) we must include that keyword
        in the mapping

        ```python
        _build_multipart_file_map(
            variables={"folder": {"files": [None, None]}},
            files={"file1": file1, "file2": file2},
        )
        # {
        #     "file1": ["variables.files.folder.files.0"],
        #     "file2": ["variables.files.folder.files.1"]
        # }
        ```

        If `variables` includes both a list of files and other single values, we must
        map them accordingly

        ```python
        _build_multipart_file_map(
            variables={"files": [None, None], "textFile": None},
            files={"file1": file1, "file2": file2, "textFile": file3},
        )
        # {
        #     "file1": ["variables.files.0"],
        #     "file2": ["variables.files.1"],
        #     "textFile": ["variables.textFile"],
        # }
        ```
        """
        map: dict[str, list[str]] = {}

        # Pre-create a list of file keys for O(1) access instead of iterator
        file_keys = list(files.keys())
        file_key_idx = 0

        for key, values in variables.items():
            reference = key
            variable_values = values

            # In case of folders the variables will look like
            # `{"folder": {"files": ...]}}`
            if isinstance(values, dict):
                folder_key = next(iter(values.keys()))
                reference += f".{folder_key}"
                # the list of file is inside the folder keyword
                variable_values = variable_values[folder_key]

            # If the variable is an array of files we must number the keys
            if isinstance(variable_values, list):
                n = len(variable_values)
                if file_key_idx + n > len(file_keys):
                    raise KeyError("Not enough file keys to match list in variables")
                for index in range(n):
                    k = file_keys[file_key_idx]
                    file_key_idx += 1
                    map.setdefault(k, [])
                    map[k].append(f"variables.{reference}.{index}")
            # Only map if this is actually a file (i.e., appears in files dict)
            elif key in files:
                map[key] = [f"variables.{reference}"]

        return map

    def _decode(self, response: Any, type: Literal["multipart", "json"]) -> Any:
        if type == "multipart":
            return json.loads(response.content.decode())
        return response.json()


__all__ = ["BaseGraphQLTestClient", "Body", "Response"]
