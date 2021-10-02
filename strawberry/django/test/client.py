import json
from typing import Any, Dict, Literal, Optional

from strawberry.test import BaseGraphQLTestClient, Response


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
            ref_variable = next(iter(variables))
            if isinstance(variables.get(ref_variable), dict):
                ref_variable += f".{next(iter(variables[ref_variable]))}"

            if len(kwargs) == 1:
                file_map = json.dumps({ref_variable: [f"variables.{ref_variable}"]})
            else:
                file_map = json.dumps(
                    {
                        k: [f"variables.{ref_variable}.{index}"]
                        for index, k in enumerate(kwargs)
                    }
                )

            body = {
                "operations": json.dumps(body),
                "map": file_map,
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
