from strawberry.schema_directive import Location, schema_directive

from .field import field


@schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
        Location.INTERFACE,
        Location.SCALAR,
        Location.ENUM,
    ],
    name="semanticNonNull",
    print_definition=True,
)
class SemanticNonNull:
    levels: list[int] = field(default_factory=lambda: [1])
