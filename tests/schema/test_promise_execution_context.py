import strawberry
from strawberry.promise import Promise
from strawberry.promise.dataloader import PromiseDataLoader
from strawberry.schema.execute_context import ExecutionContextWithPromise


def idx(keys):
    return Promise.resolve(keys)


def test_batches_correct(mocker):
    mock_loader = mocker.Mock(side_effect=idx)

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
        context_value={"dataloader": PromiseDataLoader(mock_loader)},
    )
    assert not result.errors
    assert result.data == {"id1": "1", "id2": "2"}
    mock_loader.assert_called_once_with(["1", "2"])


def test_handles_promise_and_plain(mocker):
    mock_loader = mocker.Mock(side_effect=idx)

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
        context_value={"dataloader": PromiseDataLoader(mock_loader)},
    )
    assert not result.errors
    assert result.data == {"hello": "world", "id1": "1", "id2": "2"}
    mock_loader.assert_called_once_with(["1", "2"])


def test_batches_multiple_loaders(mocker):
    location_mock_loader = mocker.Mock(side_effect=idx)
    company_mock_loader = mocker.Mock(side_effect=idx)

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
            "company_dataloader": PromiseDataLoader(company_mock_loader),
            "location_dataloader": PromiseDataLoader(location_mock_loader),
        },
    )
    assert not result.errors
    assert result.data == {
        "company1": {"id": "1", "location": {"id": "location-1"}},
        "company2": {"id": "2", "location": {"id": "location-2"}},
    }
    company_mock_loader.assert_called_once_with(["1", "2"])
    location_mock_loader.assert_called_once_with(["location-1", "location-2"])


def test_multiple_levels(mocker):
    global Company

    location_mock_loader = mocker.Mock(side_effect=idx)
    company_mock_loader = mocker.Mock(side_effect=idx)

    @strawberry.type
    class Location:
        id: str
        company_key: strawberry.Private(str)

        @strawberry.field
        def company(self, info) -> "Company":
            return (
                info.context["company_loader"]
                .load(self.company_key)
                .then(lambda id: Company(id=id))
            )

    @strawberry.type
    class Company:
        id: str

        @strawberry.field
        def location(self, info) -> Location:
            return (
                info.context["location_loader"]
                .load(f"location-{self.id}")
                .then(lambda id: Location(id=id, company_key=self.id))
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def get_company(self, info, id: str) -> Company:
            return (
                info.context["company_loader"].load(id).then(lambda id: Company(id=id))
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
                    company {
                        id
                        location {
                            id
                        }
                    }
                }
            }
            company2: getCompany(id: "2") {
                id
                location {
                    id
                    company {
                        id
                        location {
                            id
                        }
                    }
                }
            }
        }
    """,
        context_value={
            "company_loader": PromiseDataLoader(load_fn=company_mock_loader),
            "location_loader": PromiseDataLoader(load_fn=location_mock_loader),
        },
    )
    assert not result.errors
    assert result.data == {
        "company1": {
            "id": "1",
            "location": {
                "id": "location-1",
                "company": {"id": "1", "location": {"id": "location-1"}},
            },
        },
        "company2": {
            "id": "2",
            "location": {
                "id": "location-2",
                "company": {"id": "2", "location": {"id": "location-2"}},
            },
        },
    }
    company_mock_loader.assert_called_once_with(["1", "2"])
    location_mock_loader.assert_called_once_with(["location-1", "location-2"])


def test_return_error(mocker):
    def idx(keys):
        return Promise.reject(ValueError("An error"))

    mock_loader = mocker.Mock(side_effect=idx)

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
        context_value={"dataloader": PromiseDataLoader(mock_loader)},
    )
    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == "An error"


def test_raise_error(mocker):
    def idx(keys):
        raise ValueError("An error")

    mock_loader = mocker.Mock(side_effect=idx)

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
        context_value={"dataloader": PromiseDataLoader(mock_loader)},
    )
    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == "An error"
