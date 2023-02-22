import strawberry


def test_field_descriptions():
    description = "this description is super cool"

    field = strawberry.field(description=description)

    assert field.description == description
