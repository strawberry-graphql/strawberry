from typing import Any, Dict, cast

import strawberry
from strawberry.field import StrawberryField


def test_simple_custom_field():
    class UpperCaseField(StrawberryField):
        def get_result(self, source: Any, info: Any, arguments: Dict[str, Any]) -> str:
            result = super().get_result(source, info, arguments)
            return cast(str, result).upper()

    @strawberry.type
    class Query:
        name: str = UpperCaseField(default="Patrick")

        @UpperCaseField()
        def alt_name() -> str:
            return "patrick91"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ name, altName }", root_value=Query())

    assert not result.errors
    assert result.data
    assert result.data["name"] == "PATRICK"
    assert result.data["altName"] == "PATRICK91"
