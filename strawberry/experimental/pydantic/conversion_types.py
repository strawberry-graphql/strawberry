from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Type, TypeVar
from typing_extensions import Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    from strawberry.types.types import StrawberryObjectDefinition


PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


class StrawberryTypeFromPydantic(Protocol[PydanticModel]):
    """This class does not exist in runtime.
    It only makes the methods below visible for IDEs"""

    def __init__(self, **kwargs: Any):
        ...

    @staticmethod
    def from_pydantic(
        instance: PydanticModel, extra: Optional[Dict[str, Any]] = None
    ) -> StrawberryTypeFromPydantic[PydanticModel]:
        ...

    def to_pydantic(self, **kwargs: Any) -> PydanticModel:
        ...

    @property
    def __strawberry_definition__(self) -> StrawberryObjectDefinition:
        ...

    @property
    def _pydantic_type(self) -> Type[PydanticModel]:
        ...
