from typing import List, Optional

from strawberry import directive_field
from strawberry.schema_directive import Location, schema_directive
from strawberry.unset import UNSET

from .types import FieldSet, LinkImport, LinkPurpose


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
    resolvable: Optional[bool] = True


@schema_directive(
    locations=[Location.FIELD_DEFINITION, Location.OBJECT], name="shareable"
)
class Shareable:
    ...


@schema_directive(locations=[Location.SCHEMA], name="link", repeatable=True)
class Link:
    url: Optional[str]
    as_: Optional[str] = directive_field(name="as")
    for_: Optional[LinkPurpose] = directive_field(name="for")
    import_: Optional[List[Optional[LinkImport]]] = directive_field(name="import")

    def __init__(
        self,
        url: Optional[str] = UNSET,
        as_: Optional[str] = UNSET,
        for_: Optional[LinkPurpose] = UNSET,
        import_: Optional[List[Optional[LinkImport]]] = UNSET,
    ):
        self.url = url
        self.as_ = as_
        self.for_ = for_
        self.import_ = import_


@schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
        Location.INTERFACE,
        Location.OBJECT,
        Location.UNION,
        Location.ARGUMENT_DEFINITION,
        Location.SCALAR,
        Location.ENUM,
        Location.ENUM_VALUE,
        Location.INPUT_OBJECT,
        Location.INPUT_FIELD_DEFINITION,
    ],
    name="tag",
)
class Tag:
    name: str


@schema_directive(locations=[Location.FIELD_DEFINITION], name="override")
class Override:
    override_from: str = directive_field(name="from")


@schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
        Location.INTERFACE,
        Location.UNION,
        Location.ARGUMENT_DEFINITION,
        Location.SCALAR,
        Location.ENUM,
        Location.ENUM_VALUE,
        Location.INPUT_OBJECT,
        Location.INPUT_FIELD_DEFINITION,
    ],
    name="inaccessible",
)
class Inaccessible:
    ...
