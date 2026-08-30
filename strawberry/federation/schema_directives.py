from dataclasses import dataclass
from typing import ClassVar

from strawberry import directive_field
from strawberry.schema_directive import Location, schema_directive
from strawberry.types.unset import UNSET

from .types import (
    FieldSet,
    LinkImport,
    LinkPurpose,
)
from .versions import FederationVersion


@dataclass
class ImportedFrom:
    name: str
    url: str = "https://specs.apollo.dev/federation/v2.7"

    def with_version(self, version: str) -> "ImportedFrom":
        """Return a new ImportedFrom with the URL updated for the given version."""
        return ImportedFrom(
            name=self.name, url=f"https://specs.apollo.dev/federation/{version}"
        )


class FederationDirective:
    imported_from: ClassVar[ImportedFrom]
    minimum_version: ClassVar[FederationVersion]


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="external", print_definition=False
)
class External(FederationDirective):
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="external", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 0)


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="requires", print_definition=False
)
class Requires(FederationDirective):
    fields: FieldSet
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="requires", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 0)


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="provides", print_definition=False
)
class Provides(FederationDirective):
    fields: FieldSet
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="provides", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 0)


@schema_directive(
    locations=[Location.OBJECT, Location.INTERFACE],
    name="key",
    repeatable=True,
    print_definition=False,
)
class Key(FederationDirective):
    fields: FieldSet
    resolvable: bool | None = True
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="key", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 0)


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
    minimum_version: ClassVar[FederationVersion] = (2, 0)


@schema_directive(
    locations=[Location.SCHEMA], name="link", repeatable=True, print_definition=False
)
class Link:
    url: str | None
    as_: str | None = directive_field(name="as")
    for_: LinkPurpose | None = directive_field(name="for")
    import_: list[LinkImport | None] | None = directive_field(name="import")

    def __init__(
        self,
        url: str | None = UNSET,
        as_: str | None = UNSET,
        for_: LinkPurpose | None = UNSET,
        import_: list[LinkImport | None] | None = UNSET,
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
    minimum_version: ClassVar[FederationVersion] = (2, 0)


@schema_directive(
    locations=[Location.FIELD_DEFINITION], name="override", print_definition=False
)
class Override(FederationDirective):
    override_from: str = directive_field(name="from")
    label: str | None = UNSET
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="override", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 0)


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
    minimum_version: ClassVar[FederationVersion] = (2, 0)


@schema_directive(
    locations=[Location.SCHEMA], name="composeDirective", print_definition=False
)
class ComposeDirective(FederationDirective):
    name: str
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="composeDirective", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 1)


@schema_directive(
    locations=[Location.OBJECT], name="interfaceObject", print_definition=False
)
class InterfaceObject(FederationDirective):
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="interfaceObject", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 3)


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
    minimum_version: ClassVar[FederationVersion] = (2, 5)


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
    minimum_version: ClassVar[FederationVersion] = (2, 5)


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
    minimum_version: ClassVar[FederationVersion] = (2, 6)


@schema_directive(
    locations=[Location.OBJECT, Location.INTERFACE, Location.UNION],
    name="context",
    print_definition=False,
)
class Context(FederationDirective):
    name: str
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="context", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 8)


@schema_directive(
    locations=[Location.ARGUMENT_DEFINITION],
    name="fromContext",
    print_definition=False,
)
class FromContext(FederationDirective):
    field: str
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="fromContext", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 8)


@schema_directive(
    locations=[
        Location.ARGUMENT_DEFINITION,
        Location.ENUM,
        Location.FIELD_DEFINITION,
        Location.INPUT_FIELD_DEFINITION,
        Location.OBJECT,
        Location.SCALAR,
        Location.ENUM,
    ],
    name="cost",
    print_definition=False,
)
class Cost(FederationDirective):
    weight: int
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="cost", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 9)


@schema_directive(
    locations=[Location.FIELD_DEFINITION],
    name="listSize",
    print_definition=False,
)
class ListSize(FederationDirective):
    assumed_size: int | None = directive_field(name="assumedSize")
    slicing_arguments: list[str] | None = directive_field(name="slicingArguments")
    sized_fields: list[str] | None = directive_field(name="sizedFields")
    require_one_slicing_argument: bool | None = True
    imported_from: ClassVar[ImportedFrom] = ImportedFrom(
        name="listSize", url="https://specs.apollo.dev/federation/v2.7"
    )
    minimum_version: ClassVar[FederationVersion] = (2, 9)


__all__ = [
    "Authenticated",
    "ComposeDirective",
    "External",
    "FederationDirective",
    "ImportedFrom",
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
