import asyncio

from strawberry.http.async_base_view import WSConnectionParams


class WebsocketsMixin:
    """
    A mixin for the view class to implement test functionality
    """

    async def on_ws_connect(self, params: WSConnectionParams) -> None:
        # default behaviour
        if not params.connection_params:
            return None
        # 1. Add a member to the payload, and hence, connection_params
        if "add" in params.connection_params:
            params.connection_params["added"] = True
        # 2. Reject if payload contains "reject-me"
        if "reject-me" in params.connection_params:
            return await params.reject()
        # 3. spend time evaluating
        if "sleep" in params.connection_params:
            await asyncio.sleep(float(params.connection_params["sleep"]))
        # 4. return any response in the payload
        if "response" in params.connection_params:
            params.response_params = params.connection_params["response"]
        return None
