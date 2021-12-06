from typing import Any

from strawberry.asgi.handlers import (
    GraphQLTransportWSHandler as BaseGraphQLTransportWSHandler,
)


class GraphQLTransportWSHandler(BaseGraphQLTransportWSHandler):
    async def get_context(self) -> Any:
        return await self._get_context()

    async def get_root_value(self) -> Any:
        return await self._get_root_value()
