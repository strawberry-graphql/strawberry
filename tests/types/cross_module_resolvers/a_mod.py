import strawberry


def a_resolver() -> list["AObject"]:
    return []


@strawberry.type
class ABase:
    a_name: str


@strawberry.type
class AObject(ABase):
    a_age: int

    @strawberry.field
    def a_is_of_full_age(self) -> bool:
        return self.a_age >= 18
