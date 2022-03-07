from strawberry.custom_scalar import scalar
from strawberry.schema_directive import Location, schema_directive


FieldSet = scalar(str, name="_FieldSet")


@schema_directive(locations=[Location.FIELD_DEFINITION], name="external")
class External:
    ...


@schema_directive(locations=[Location.FIELD_DEFINITION], name="requires")
class Requires:
    fields: FieldSet


@schema_directive(locations=[Location.FIELD_DEFINITION], name="provides")
class Provides:
    fields: FieldSet


@schema_directive(locations=[Location.OBJECT, Location.INTERFACE], name="key")
class Key:
    fields: FieldSet
