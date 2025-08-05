from dataclasses import dataclass
from typing import ClassVar, Optional

from strawberry import directive_field
from strawberry.schema_directive import Location, schema_directive
from strawberry.types.unset import UNSET

from .types import (
    FieldSet,
    LinkImport,
    LinkPurpose,
)


@dataclass
class ImportedFrom:
    name: str
    url: str = "https://specs.apollo.dev/federation/v2.7"


class FederationDirective:
    imported_from: ClassVar[ImportedFrom]


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="external", print_definition=False
)
class External(FederationDirective):
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="external", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="requires", print_definition=False
)
class Requires(FederationDirective):
    fields: FieldSet
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="requires", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="provides", print_definition=False
)
class Provides(FederationDirective):
    fields: FieldSet
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="provides", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.OBJECT, Location.INTERFACE],
    name="key",
    repeatable=True,
    print_definition=False,
)
class Key(FederationDirective):
    fields: FieldSet
    resolvable: Optional[bool] = True
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="key", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.FIELD_DEFINITION, Location.OBJECT],
    name="shareable",
    repeatable=True,
    print_definition=False,
)
class Shareable(FederationDirective):
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="shareable", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.SCHEMA], name="link", repeatable=True, print_definition=False
)
class Link:
    url: Optional[str]
    as_: Optional[str] = directive_field(name="as")
    for_: Optional[LinkPurpose] = directive_field(name="for")
    import_: Optional[list[Optional[LinkImport]]] = directive_field(name="import")

    def __init__(
        self,
        url: Optional[str] = UNSET,
        as_: Optional[str] = UNSET,
        for_: Optional[LinkPurpose] = UNSET,
        import_: Optional[list[Optional[LinkImport]]] = UNSET,
    ) -> None:
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
    repeatable=True,
    print_definition=False,
)
class Tag(FederationDirective):
    name: str
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="tag", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="override", print_definition=False
)
class Override(FederationDirective):
    override_from: str = directive_field(name="from")
    label: Optional[str] = UNSET
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="override", url="https://specs.apollo.dev/federation/v2.7"
    )


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
    print_definition=False,
)
class Inaccessible(FederationDirective):
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="inaccessible", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.SCHEMA], name="composeDirective", print_definition=False
)
class ComposeDirective(FederationDirective):
    name: str
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="composeDirective", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[Location.OBJECT], name="interfaceObject", print_definition=False
)
class InterfaceObject(FederationDirective):
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="interfaceObject", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
        Location.INTERFACE,
        Location.SCALAR,
        Location.ENUM,
    ],
    name="authenticated",
    print_definition=False,
)
class Authenticated(FederationDirective):
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="authenticated", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
        Location.INTERFACE,
        Location.SCALAR,
        Location.ENUM,
    ],
    name="requiresScopes",
    print_definition=False,
)
class RequiresScopes(FederationDirective):
    scopes: "list[list[str]]"
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="requiresScopes", url="https://specs.apollo.dev/federation/v2.7"
    )


@schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
        Location.INTERFACE,
        Location.SCALAR,
        Location.ENUM,
    ],
    name="policy",
    print_definition=False,
)
class Policy(FederationDirective):
    policies: "list[list[str]]"
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="policy", url="https://specs.apollo.dev/federation/v2.7"
    )


__all__ = [
    "Authenticated",
    "ComposeDirective",
    "External",
    "Inaccessible",
    "InterfaceObject",
    "Key",
    "Link",
    "Override",
    "Policy",
    "Provides",
    "Requires",
    "RequiresScopes",
    "Shareable",
    "Tag",
]
