from strawberry.schema_directive import Location, schema_directive


@schema_directive(locations=[Location.INPUT_OBJECT], name="oneOf")
class OneOf: ...


__all__ = ["OneOf"]
