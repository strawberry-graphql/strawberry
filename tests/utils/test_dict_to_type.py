import strawberry
from strawberry.utils.dict_to_type import dict_to_type


def test_simple_type():
    @strawberry.input
    class SearchInput:
        query: str

    data = {"query": "Example"}

    converted = dict_to_type(data, SearchInput)

    assert type(converted) == SearchInput
    assert converted.query == "Example"


def test_nested():
    @strawberry.input
    class Meta:
        x: str

    @strawberry.input
    class SearchInput:
        query: str
        meta: Meta

    data = {"query": "Example", "meta": {"x": "demo"}}

    converted = dict_to_type(data, SearchInput)

    assert type(converted) == SearchInput
    assert converted.meta.x == "demo"
