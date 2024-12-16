from typing import TypeVar
from typing_extensions import Annotated

STRAWBERRY_REQUIRED_TOKEN = "strawberry_required"

T = TypeVar("T")

NonNull = Annotated[T, STRAWBERRY_REQUIRED_TOKEN]
