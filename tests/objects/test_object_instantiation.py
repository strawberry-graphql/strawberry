import strawberry


def test_can_instantiate_types_directly():
    @strawberry.type
    class User:
        username: str

        @strawberry.field
        def email(self) -> str:
            return self.username + "@somesite.com"

    user = User(username="abc")
    assert user.username == "abc"
    assert user.email() == "abc@somesite.com"
