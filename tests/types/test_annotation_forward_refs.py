from __future__ import annotations

from typing_extensions import Annotated

import pytest

import strawberry


@pytest.mark.xfail(reason="future references support missing", strict=True)
def test_annotated_is_preserved():
    @strawberry.type
    class SomeType:
        foo: Annotated[str, "foo"]
        bar: Annotated[str, "bar"] = strawberry.field(graphql_type=int)

    assert SomeType.__annotations__ == {
        "foo": "Annotated[str, 'foo']",
        "bar": "Annotated[int, 'bar']",
    }
