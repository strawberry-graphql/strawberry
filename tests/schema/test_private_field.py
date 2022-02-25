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

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
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


def test_private_field_with_str_annotations():
    """Check compatibility of strawberry.Private with annotations as string."""

    from dataclasses import dataclass

    @strawberry.type
    class Query:
        not_seen: "strawberry.Private[SensitiveData]"

        @strawberry.field
        def accesible_info(self) -> str:
            return self.not_seen.info

    @dataclass
    class SensitiveData:
        value: int
        info: str

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "query { accesibleInfo }", root_value=Query(not_seen=SensitiveData(1, "foo"))
    )
    assert result.data == {"accesibleInfo": "foo"}
