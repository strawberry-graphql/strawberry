import strawberry


def b_resolver() -> list["BObject"]:
    return []


@strawberry.type
class BBase:
    b_name: str = strawberry.field()


@strawberry.type
class BObject(BBase):
    b_age: int = strawberry.field()

    @strawberry.field
    def b_is_of_full_age(self) -> bool:
        return self.b_age >= 18
