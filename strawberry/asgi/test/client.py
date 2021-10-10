import json
from typing import Any, Dict, Optional

from typing_extensions import Literal

from strawberry.test import GraphQLTestClient as BaseGraphQLTestClient


class GraphQLTestClient(BaseGraphQLTestClient):
    def _build_body(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        body: Dict[str, Any] = {"query": query}

        if variables:
            body["variables"] = variables

        if files:
            assert variables is not None
            assert files is not None
            file_map = GraphQLTestClient._build_multipart_file_map(variables, files)

            body = {
                "operations": json.dumps(body),
                "map": json.dumps(file_map),
            }
        return body

    def _request(
        self,
        body: Dict[str, Any],
        headers: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ):

        return self._client.post("/graphql/", data=body, files=files, headers=headers)

    def _decode(self, response, type: Literal["multipart", "json"]):
        return response.json()
