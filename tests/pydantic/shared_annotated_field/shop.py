import pydantic

import strawberry

from .aliases import AddressField


@strawberry.type(name="ShopAddress")
class Address:
    street: str


@strawberry.pydantic.type
class Shop(pydantic.BaseModel):
    address: AddressField
