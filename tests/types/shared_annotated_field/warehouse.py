import strawberry

from .aliases import AddressField


@strawberry.type(name="WarehouseAddress")
class Address:
    dock: int


@strawberry.type
class Warehouse:
    address: AddressField
