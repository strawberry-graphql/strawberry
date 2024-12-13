from typing import Optional

from strawberry.schema_directive import Location, schema_directive


@schema_directive(
    locations=[Location.FIELD_DEFINITION],
    name="semanticNonNull",
    print_definition=True,
)
class SemanticNonNull:
    level: Optional[int] = None
