from typing import Union

from strawberry import UNSET
from strawberry.exceptions import ConnectionRejectionError
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.typevars import (
    Request,
    Response,
    SubResponse,
    WebSocketRequest,
    WebSocketResponse,
)
from strawberry.types.unset import UnsetType


class OnWSConnectMixin(
    AsyncBaseHTTPView[
        Request,
        Response,
        SubResponse,
        WebSocketRequest,
        WebSocketResponse,
        dict[str, object],
        object,
    ]
):
    async def on_ws_connect(
        self, context: dict[str, object]
    ) -> Union[UnsetType, None, dict[str, object]]:
        connection_params = context["connection_params"]

        if isinstance(connection_params, dict):
            if connection_params.get("test-reject"):
                if "err-payload" in connection_params:
                    raise ConnectionRejectionError(connection_params["err-payload"])
                raise ConnectionRejectionError

            if connection_params.get("test-accept"):
                if "ack-payload" in connection_params:
                    return connection_params["ack-payload"]
                return UNSET

            if connection_params.get("test-modify"):
                connection_params["modified"] = True
                return UNSET

        return await super().on_ws_connect(context)
