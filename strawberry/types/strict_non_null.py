from typing import Annotated, TypeVar

STRAWBERRY_REQUIRED_TOKEN = "strawberry_required"

T = TypeVar("T")

NonNull = Annotated[T, STRAWBERRY_REQUIRED_TOKEN]
