import json
from typing import Callable

from . import GraphQLHTTPResponse


JsonEncoder = Callable[[GraphQLHTTPResponse], str]


def default_json_encoder(data: GraphQLHTTPResponse) -> str:
    return json.dumps(data)
