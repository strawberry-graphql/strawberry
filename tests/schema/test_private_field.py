import pytest

import strawberry
from strawberry.exceptions import PrivateStrawberryFieldError


def test_private_field():
    @strawberry.type
    class Query:
        name: str
        age: strawberry.Private[int]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str

    instance = Query(name="Luke", age=22)
    assert instance.name == "Luke"
    assert instance.age == 22


def test_private_field_with_strawberry_field_error():
    with pytest.raises(PrivateStrawberryFieldError) as error:

        @strawberry.type
        class Query:
            name: str
            age: strawberry.Private[int] = strawberry.field(description="🤫")

    assert "Field age on type Query" in str(error)


def test_private_field_access_in_resolver():
    @strawberry.type
    class Query:
        name: str
        age: strawberry.Private[int]

        @strawberry.field
        def age_in_months(self) -> int:
            return self.age * 12

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "query { ageInMonths }", root_value=Query(name="Dave", age=7)
    )

    assert not result.errors
    assert result.data == {
        "ageInMonths": 84,
    }
