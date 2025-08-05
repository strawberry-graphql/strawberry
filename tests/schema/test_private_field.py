from dataclasses import dataclass
from typing import Generic, TypeVar

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import PrivateStrawberryFieldError
from strawberry.types.field import StrawberryField


def test_private_field():
    @strawberry.type
    class Query:
        name: str
        age: strawberry.Private[int]

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type is str

    instance = Query(name="Luke", age=22)
    assert instance.name == "Luke"
    assert instance.age == 22


@pytest.mark.raises_strawberry_exception(
    PrivateStrawberryFieldError,
    match=("Field age on type Query cannot be both private and a strawberry.field"),
)
def test_private_field_with_strawberry_field_error():
    @strawberry.type
    class Query:
        name: str
        age: strawberry.Private[int] = strawberry.field(description="🤫")


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


@strawberry.type
class Query:
    not_seen: "strawberry.Private[SensitiveData]"

    @strawberry.field
    def accessible_info(self) -> str:
        return self.not_seen.info


@dataclass
class SensitiveData:
    value: int
    info: str


def test_private_field_with_str_annotations():
    """Check compatibility of strawberry.Private with annotations as string."""
    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "query { accessibleInfo }",
        root_value=Query(not_seen=SensitiveData(1, "foo")),
    )
    assert result.data == {"accessibleInfo": "foo"}

    # Check if querying `notSeen` raises error and no data is returned
    assert "notSeen" not in str(schema)
    failed_result = schema.execute_sync(
        "query { notSeen }", root_value=Query(not_seen=SensitiveData(1, "foo"))
    )
    assert failed_result.data is None


def test_private_field_defined_outside_module_scope():
    """Check compatibility of strawberry.Private when defined outside module scope."""
    global LocallyScopedSensitiveData

    @strawberry.type
    class LocallyScopedQuery:
        not_seen: "strawberry.Private[LocallyScopedSensitiveData]"

        @strawberry.field
        def accessible_info(self) -> str:
            return self.not_seen.info

    @dataclass
    class LocallyScopedSensitiveData:
        value: int
        info: str

    schema = strawberry.Schema(query=LocallyScopedQuery)

    assert "notSeen" not in str(schema)

    del LocallyScopedSensitiveData


def test_private_field_type_resolution_with_generic_type():
    """Check strawberry.Private when its argument is a implicit `Any` generic type.

    Refer to: https://github.com/strawberry-graphql/strawberry/issues/1938
    """
    T = TypeVar("T")

    class GenericPrivateType(Generic[T]):
        pass

    private_field = StrawberryField(
        type_annotation=StrawberryAnnotation(
            annotation="strawberry.Private[GenericPrivateType]",
            namespace={**globals(), **locals()},
        ),
    )
    assert private_field.type == strawberry.Private[GenericPrivateType]
