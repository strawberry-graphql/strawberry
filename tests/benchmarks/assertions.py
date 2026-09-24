from strawberry.types import ExecutionResult


def assert_items(result: ExecutionResult, count: int) -> None:
    assert result.errors is None
    assert result.data == {
        "items": [{"name": "Item", "index": i} for i in range(count)]
    }


def assert_people(result: ExecutionResult, *, uppercase: bool = False) -> None:
    assert result.errors is None
    assert result.data is not None
    assert len(result.data["people"]) == 100
    for i, person in enumerate(result.data["people"]):
        assert person == {
            "age": i,
            "description": f"Description {i}",
            "address": f"Address {i}",
            "name": f"Person {i}",
            **{
                f"prop{letter.upper()}": (
                    f"Prop {letter.upper()} {i}".upper()
                    if uppercase and letter in "gh"
                    else f"Prop {letter.upper()} {i}"
                )
                for letter in "abcdefghij"
            },
        }
