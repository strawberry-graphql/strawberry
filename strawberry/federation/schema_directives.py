from typing_extensions import Literal

from strawberry import directive_field
from strawberry.custom_scalar import scalar
from strawberry.schema_directive import Location, schema_directive


FieldSet = scalar(str, name="_FieldSet")
LinkPurpose = Literal["SECURITY", "EXECUTION"]
LinkImport = scalar(list, name="link__Import")


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
    resolvable: bool = True


@schema_directive(
    locations=[Location.FIELD_DEFINITION, Location.OBJECT], name="shareable"
)
class Shareable:
    ...


@schema_directive(locations=[Location.FIELD_DEFINITION], name="tag")
class Tag:
    name: str


@schema_directive(locations=[Location.FIELD_DEFINITION], name="override")
class Override:
    override_from: str = directive_field(name="from")  # type: ignore


@schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
        Location.INTERFACE,
        Location.UNION,
    ],
    name="inaccessible",
)
class Inaccessible:
    ...
