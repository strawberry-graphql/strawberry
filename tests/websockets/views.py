import asyncio
from typing import Any, Dict, Optional, Union
from typing_extensions import Literal


class WebsocketsMixin:
    """
    A mixin for the view class to implement test functionality
    """

    async def on_ws_connect(
        self, connection_params: Optional[Dict[str, Any]]
    ) -> Union[Literal[False], None, Dict[str, Any]]:
        # default behaviour
        if not connection_params:
            return None
        # 1. Add a member to the payload, and hence, connection_params
        if "add" in connection_params:
            connection_params["added"] = True
        # 2. Reject if payload contains "reject-me"
        if "reject-me" in connection_params:
            return False
        # 3. spend time evaluating
        if "sleep" in connection_params:
            await asyncio.sleep(float(connection_params["sleep"]))
        # 4. return any response in the payload
        if "response" in connection_params:
            return connection_params["response"]
        return None
