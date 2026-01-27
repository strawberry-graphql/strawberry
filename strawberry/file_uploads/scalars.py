from typing import NewType

from strawberry.types.scalar import scalar

Upload = NewType("Upload", bytes)

UploadDefinition = scalar(
    name="Upload",
    description="Represents a file upload.",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

__all__ = ["Upload", "UploadDefinition"]
