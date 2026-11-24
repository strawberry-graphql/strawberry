import pydantic

import strawberry

from .aliases import AddressField


@strawberry.type(name="WarehouseAddress")
class Address:
    dock: int


@strawberry.pydantic.type
class Warehouse(pydantic.BaseModel):
    address: AddressField
