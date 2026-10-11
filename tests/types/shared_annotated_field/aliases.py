from typing import Annotated

import strawberry

# `Address` is resolved in the module of each type using the alias
AddressField = Annotated[str, strawberry.field(graphql_type="Address")]
