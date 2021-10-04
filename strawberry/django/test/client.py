import json
from typing import Any, Dict, Optional

from typing_extensions import Literal

from strawberry.test import BaseGraphQLTestClient, Response


def _build_multipart_file_map(variables, kwargs):
    map = {}
    for key, values in variables.items():
        reference = key
        files = values

        # In case of folders the variables will look like `{"folder": {"files": ...]}}`
        if isinstance(values, dict):
            files_key = list(values.keys())[0]
            reference += f".{files_key}"
            # the list of file is inside the folder keyword
            files = values[files_key]

        # If the variable is an array of files we must number the keys
        if isinstance(files, list):
            # copying `kwargs` as when we map a file we must discard from the dict
            _kwargs = kwargs.copy()
            for index, _ in enumerate(files):
                k = list(_kwargs.keys())[0]
                _kwargs.pop(k)
                map.setdefault(k, [])
                map[k].append(f"variables.{reference}.{index}")
        else:
            map[key] = [f"variables.{reference}"]

    return map


class GraphQLTestClient(BaseGraphQLTestClient):
    def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        asserts_errors: Optional[bool] = True,
        format: Literal["multipart", "json"] = "json",
        **kwargs,
    ) -> Response:
        body: Any = {"query": query}

        if variables:
            body["variables"] = variables

        if format == "multipart":
            assert variables is not None
            file_map = _build_multipart_file_map(variables, kwargs)

            body = {
                "operations": json.dumps(body),
                "map": json.dumps(file_map),
                **kwargs,
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
