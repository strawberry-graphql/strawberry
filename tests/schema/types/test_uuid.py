import uuid

import strawberry


def test_uuid():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_uuid_out(self) -> uuid.UUID:
            return uuid.NAMESPACE_DNS

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ exampleUuidOut }")

    assert not result.errors
    assert result.data["exampleUuidOut"] == str(uuid.NAMESPACE_DNS)


def test_uuid_as_input():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_uuid_in(self, uid: uuid.UUID) -> uuid.UUID:
            return uid

    schema = strawberry.Schema(Query)

    result = schema.execute_sync(
        f'{{ exampleUuidIn(uid: "{str(uuid.NAMESPACE_DNS)}") }}'
    )

    assert not result.errors
    assert result.data["exampleUuidIn"] == str(uuid.NAMESPACE_DNS)
