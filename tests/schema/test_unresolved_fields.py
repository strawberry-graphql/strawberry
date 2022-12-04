import pytest

import strawberry
from strawberry.exceptions.unresolved_field_type import UnresolvedFieldTypeError


@pytest.mark.raises_strawberry_exception(
    UnresolvedFieldTypeError,
    match=(
        "Could not resolve the type of 'user'. Check that "
        "the class is accessible from the global module scope."
    ),
)
def test_unresolved_field_fails():
    @strawberry.type
    class Query:
        user: "User"  # type: ignore  # noqa: F821

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    UnresolvedFieldTypeError,
    match=(
        "Could not resolve the type of 'user'. Check that "
        "the class is accessible from the global module scope."
    ),
)
def test_unresolved_field_with_resolver_fails():
    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> "User":  # type: ignore  # noqa: F821
            ...

    strawberry.Schema(query=Query)
