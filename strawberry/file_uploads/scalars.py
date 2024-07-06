from typing import NewType

from strawberry.types.scalar import scalar

Upload = scalar(NewType("Upload", bytes), parse_value=lambda x: x)

__all__ = ["Upload"]
