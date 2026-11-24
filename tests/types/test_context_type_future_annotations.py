from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from tests.types.test_context_type import MyContext


def test_context_parameter_with_string_annotation():
    @strawberry.type
    class Query:
        @strawberry.field
        def user_id(self, context: strawberry.Context[MyContext]) -> str:
            return context.user_id

    schema = strawberry.Schema(query=Query)

    assert "userId: String!" in str(schema)
    assert "context" not in str(schema)

    from tests.types.test_context_type import MyContext as RuntimeContext

    result = schema.execute_sync(
        "{ userId }", context_value=RuntimeContext(user_id="7")
    )
    assert not result.errors
    assert result.data == {"userId": "7"}
