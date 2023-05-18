from typing import Any, Dict, Optional, Union

from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from strawberry.asgi import GraphQL as BaseGraphQL
from tests.views.schema import Query, schema


class GraphQL(BaseGraphQL):
    async def get_root_value(self, request) -> Query:
        return Query()

    async def get_context(
        self,
        request: Union[Request, WebSocket],
        response: Optional[Response] = None,
    ) -> Dict[str, Union[Request, WebSocket, Response, str, None]]:
        return {"request": request, "response": response, "custom_value": "Hi"}


def create_app(**kwargs: Any) -> GraphQL:
    return GraphQL(schema, **kwargs)
