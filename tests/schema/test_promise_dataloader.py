import strawberry
from strawberry.promise import Promise
from strawberry.promise.dataloader import PromiseDataLoader
from strawberry.schema.execute_context import ExecutionContextWithPromise


def test_batches_correct():
    load_calls = []

    def load_fn(keys):
        load_calls.append(keys)
        return Promise.resolve(keys)

    loader = PromiseDataLoader(load_fn)

    @strawberry.type
    class Query:
        @strawberry.field
        def get_id(self, info, id: str) -> str:
            return info.context["dataloader"].load(id)

    schema = strawberry.Schema(
        query=Query, execution_context_class=ExecutionContextWithPromise
    )
    result = schema.execute_sync(
        """
        query {
            id1: getId(id: "1")
            id2: getId(id: "2")
        }
    """,
        context_value={"dataloader": loader},
    )
    assert not result.errors
    assert result.data == {"id1": "1", "id2": "2"}
    assert load_calls == [["1", "2"]]


def test_handles_promise_and_plain():
    load_calls = []

    def load_fn(keys):
        load_calls.append(keys)
        return Promise.resolve(keys)

    loader = PromiseDataLoader(load_fn)

    @strawberry.type
    class Query:
        @strawberry.field
        def get_id(self, info, id: str) -> str:
            return info.context["dataloader"].load(id)

        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, execution_context_class=ExecutionContextWithPromise
    )
    result = schema.execute_sync(
        """
        query {
            hello
            id1: getId(id: "1")
            id2: getId(id: "2")
        }
    """,
        context_value={"dataloader": loader},
    )
    assert not result.errors
    assert result.data == {"hello": "world", "id1": "1", "id2": "2"}
    assert load_calls == [["1", "2"]]


def test_batches_multiple_loaders():
    location_load_calls = []
    company_load_calls = []

    def location_load_fn(keys):
        location_load_calls.append(keys)
        return Promise.resolve(keys)

    location_loader = PromiseDataLoader(location_load_fn)

    def company_load_fn(keys):
        company_load_calls.append(keys)
        return Promise.resolve(keys)

    company_loader = PromiseDataLoader(company_load_fn)

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

    schema = strawberry.Schema(
        query=Query, execution_context_class=ExecutionContextWithPromise
    )
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
            "company_dataloader": company_loader,
            "location_dataloader": location_loader,
        },
    )
    assert not result.errors
    assert result.data == {
        "company1": {"id": "1", "location": {"id": "location-1"}},
        "company2": {"id": "2", "location": {"id": "location-2"}},
    }
    assert company_load_calls == [["1", "2"]]
    assert location_load_calls == [["location-1", "location-2"]]
