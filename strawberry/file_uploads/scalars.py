from typing import NewType

from ..custom_scalar import scalar

Upload = scalar(NewType("Upload", bytes), parse_value=lambda x: x)
