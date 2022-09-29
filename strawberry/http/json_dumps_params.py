from typing import Callable, Optional, Tuple

from typing_extensions import TypedDict


class JSONDumpsParams(TypedDict, total=False):
    skipkeys: bool
    ensure_ascii: bool
    check_circular: bool
    allow_nan: bool
    indent: Optional[int]
    separators: Optional[Tuple[str, str]]
    default: Callable[[object], object]
    sort_keys: bool
