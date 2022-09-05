import pytest

import strawberry
from strawberry.exceptions.unresolved_field_type import UnresolvedFieldTypeError


@pytest.mark.raises_strawberry_exception(
    UnresolvedFieldTypeError,
    message="strawberry.enum can only be used with subclasses of Enum. ",
)
def test_unresolved_field_fails():
    @strawberry.type
    class Query:
        user: "User"  # type: ignore  # noqa: F821

    strawberry.Schema(query=Query)
