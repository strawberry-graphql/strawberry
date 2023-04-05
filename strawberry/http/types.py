from typing import List, Mapping, Optional, Union
from typing_extensions import Literal

HTTPMethod = Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"
]

QueryParams = Mapping[str, Optional[Union[str, List[str]]]]
