import strawberry

from .aliases import AddressField


@strawberry.type(name="ShopAddress")
class Address:
    street: str


@strawberry.type
class Shop:
    address: AddressField
