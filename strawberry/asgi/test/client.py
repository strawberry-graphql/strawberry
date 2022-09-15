import json
from typing import Dict, Mapping, Optional

from typing_extensions import Literal

from strawberry.test import BaseGraphQLTestClient


class GraphQLTestClient(BaseGraphQLTestClient):
    def _build_body(
        self,
        query: str,
        variables: Optional[Dict[str, Mapping]] = None,
        files: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:

        body: Dict[str, object] = {"query": query}

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

    def request(
        self,
        body: Dict[str, object],
        headers: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, object]] = None,
    ):
        return self._client.post(
            "/graphql/",
            json=body if not files else None,
            data=body if files else None,
            files=files,
            headers=headers,
        )

    def _decode(self, response, type: Literal["multipart", "json"]):
        return response.json()
