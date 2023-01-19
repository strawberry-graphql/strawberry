from __future__ import annotations

from typing import Any, Dict, Optional, TypeVar
from typing_extensions import Protocol

from pydantic import BaseModel

from strawberry.types.types import TypeDefinition

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


class StrawberryTypeFromPydantic(Protocol[PydanticModel]):
    """This class does not exist in runtime.
    It only makes the methods below visible for IDEs"""

    def __init__(self, **kwargs):
        ...

    @staticmethod
    def from_pydantic(
        instance: PydanticModel, extra: Optional[Dict[str, Any]] = None
    ) -> StrawberryTypeFromPydantic[PydanticModel]:
        ...

    def to_pydantic(self, **kwargs) -> PydanticModel:
        ...

    @property
    def _type_definition(self) -> TypeDefinition:
        ...

    @property
    def _pydantic_type(self) -> PydanticModel:
        ...
