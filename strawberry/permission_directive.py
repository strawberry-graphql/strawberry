from typing import List

from strawberry.schema_directive import Location, schema_directive


@schema_directive(
    name="RequiresPermissions",
    locations=[Location.FIELD_DEFINITION],
    description="Indicates that a field requires special permissions to be accessed",
)
class RequiresPermissionsDirective:
    permissions: List[str]
