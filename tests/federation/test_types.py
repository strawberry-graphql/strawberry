import strawberry


def test_type():
    @strawberry.federation.type(keys=["id"])
    class Location:
        id: strawberry.ID

    assert Location(id=strawberry.ID("1")).id == "1"


def test_type_and_override():
    @strawberry.federation.type(keys=["id"])
    class Location:
        id: strawberry.ID
        address: str = strawberry.federation.field(override="start")

    location = Location(id=strawberry.ID("1"), address="ABC")

    assert location.id == "1"
    assert location.address == "ABC"


def test_type_and_override_with_resolver():
    @strawberry.federation.type(keys=["id"])
    class Location:
        id: strawberry.ID
        address: str = strawberry.federation.field(
            override="start", resolver=lambda: "ABC"
        )

    location = Location(id=strawberry.ID("1"))

    assert location.id == "1"
