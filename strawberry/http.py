from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class GraphQLHTTPResponse(TypedDict, total=False):
    data: Optional[Dict[str, Any]]
    errors: Optional[List[Any]]
