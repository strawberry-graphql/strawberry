from promise import Promise
from promise.dataloader import DataLoader

import strawberry
from strawberry.schema.execute_context import ExecutionContextWithPromise


def test_batches_correct():
    load_calls = []

    class TestDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            load_calls.append(keys)
            return Promise.resolve(keys)

    @strawberry.type
    class Query:
        @strawberry.field
        def get_id(self, info, id: str) -> str:
            return info.context["dataloader"].load(id)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
        query {
            id1: getId(id: "1")
            id2: getId(id: "2")
        }
    """,
        context_value={"dataloader": TestDataLoader()},
        execution_context_class=ExecutionContextWithPromise,
    )
    assert not result.errors
    assert result.data == {"id1": "1", "id2": "2"}
    assert load_calls == [["1", "2"]]


def test_handles_promise_and_plain():
    load_calls = []

    class TestDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            load_calls.append(keys)
            return Promise.resolve(keys)

    @strawberry.type
    class Query:
        @strawberry.field
        def get_id(self, info, id: str) -> str:
            return info.context["dataloader"].load(id)

        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
        query {
            hello
            id1: getId(id: "1")
            id2: getId(id: "2")
        }
    """,
        context_value={"dataloader": TestDataLoader()},
        execution_context_class=ExecutionContextWithPromise,
    )
    assert not result.errors
    assert result.data == {"hello": "world", "id1": "1", "id2": "2"}
    assert load_calls == [["1", "2"]]


def test_batches_multiple_loaders():
    location_load_calls = []
    company_load_calls = []

    class LocationDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            location_load_calls.append(keys)
            return Promise.resolve(keys)

    class CompanyDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            company_load_calls.append(keys)
            return Promise.resolve(keys)

    @strawberry.type
    class Location:
        id: str

    @strawberry.type
    class Company:
        id: str

        @strawberry.field
        def location(self, info) -> Location:
            return (
                info.context["location_dataloader"]
                .load(f"location-{self.id}")
                .then(lambda id: Location(id=id))
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def get_company(self, info, id: str) -> Company:
            return (
                info.context["company_dataloader"]
                .load(id)
                .then(lambda id: Company(id=id))
            )

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
        query {
            company1: getCompany(id: "1") {
                id
                location {
                    id
                }
            }
            company2: getCompany(id: "2") {
                id
                location {
                    id
                }
            }
        }
    """,
        context_value={
            "company_dataloader": CompanyDataLoader(),
            "location_dataloader": LocationDataLoader(),
        },
        execution_context_class=ExecutionContextWithPromise,
    )
    assert not result.errors
    assert result.data == {
        "company1": {"id": "1", "location": {"id": "location-1"}},
        "company2": {"id": "2", "location": {"id": "location-2"}},
    }
    assert company_load_calls == [["1", "2"]]
    assert location_load_calls == [["location-1", "location-2"]]
