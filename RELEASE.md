Release type: patch

Fix the Pydantic conversion method for Enum values, and add a mechanism to specify an interface type when converting from Pydantic. The Pydantic interface is really a base dataclass for the subclasses to extend. When you do the conversion, you have to use `strawberry.experimental.pydantic.interface` to let us know that this type is an interface. You also have to use your converted interface type as the base class for the sub types as normal.
