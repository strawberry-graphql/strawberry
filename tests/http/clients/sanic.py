from __future__ import annotations

import json
from io import BytesIO
from random import randint
from typing import Dict, Optional, Union

from typing_extensions import Literal

from sanic import Sanic
from strawberry.sanic.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self):
        return Query()


class SanicHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True):
        self.app = Sanic(
            f"test_{int(randint(0, 1000))}",
            log_config={
                "version": 1,
                "loggers": {},
                "handlers": {},
            },
        )
        self.app.add_route(
            GraphQLView.as_view(schema=schema, graphiql=graphiql), "/graphql"
        )

    async def _request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        body = self._build_body(query, variables, files)

        data: Union[Dict[str, object], str, None] = None

        if body:
            data = body if files else json.dumps(body)

        request, response = await self.app.asgi_client.request(
            method, "/graphql", data=data, headers=headers, files=files, **kwargs
        )

        return Response(status_code=response.status_code, data=response.content)
