from typing import List, Mapping, Union
from typing_extensions import Literal

HTTPMethod = Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"
]

QueryParams = Mapping[str, Union[str, List[str]]]
