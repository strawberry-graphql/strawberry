from typing import Any

from strawberry.asgi.handlers import (
    GraphQLTransportWSHandler as BaseGraphQLTransportWSHandler,
)
from strawberry.fastapi.context import BaseContext


class GraphQLTransportWSHandler(BaseGraphQLTransportWSHandler):
    async def get_context(self) -> Any:
        context = await self._get_context()
        if isinstance(context, BaseContext):
            context.connection_params = self.connection_params
        return context

    async def get_root_value(self) -> Any:
        return await self._get_root_value()


__all__ = ["GraphQLTransportWSHandler"]
