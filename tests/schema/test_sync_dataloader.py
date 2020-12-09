from promise import Promise
from promise.dataloader import DataLoader

import strawberry


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
    )
    assert not result.errors
    assert result.data == {"id1": "1", "id2": "2"}
    assert load_calls == [["1", "2"]]
