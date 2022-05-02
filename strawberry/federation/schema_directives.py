from strawberry.custom_scalar import scalar
from strawberry.schema_directive import Location, schema_directive
from strawberry import directive_field
from typing import Literal


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

# @schema_directive(locations=[Location.SCHEMA], name="link")
# class Link: # todo: address this in some other PR ... it needs to be handled differently than these other directives.
#     url: str
#     link_as: str # "as" collides with Python reserved word "as"
#     link_for: LinkPurpose # "for" collides with Python reserved word "for"
#     link_import: LinkImport  # "import" is reserved word

@schema_directive(locations=[Location.FIELD_DEFINITION, Location.OBJECT], name="shareable")
class Shareable:
    ...

@schema_directive(locations=[Location.FIELD_DEFINITION], name="tag")
class Tag: # todo confirm is in fact a "schema directive" ... confirm properties of "Tag"
    name: str

@schema_directive(locations=[Location.FIELD_DEFINITION], name="override")
class Override:
    override_from: str = directive_field(name="from")

@schema_directive(
    locations=[Location.FIELD_DEFINITION, Location.OBJECT, Location.INTERFACE, Location.UNION],
    name="inaccessible")
class Inaccessible:
    ...
