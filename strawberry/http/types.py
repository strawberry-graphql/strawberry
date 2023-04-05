from typing import Any, List, Mapping, Optional, Union
from typing_extensions import Literal, TypedDict

HTTPMethod = Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"
]

QueryParams = Mapping[str, Optional[Union[str, List[str]]]]


class FormData(TypedDict):
    files: Mapping[str, Any]
    form: Mapping[str, Any]
