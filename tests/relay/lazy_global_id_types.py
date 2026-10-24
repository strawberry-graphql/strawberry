import strawberry
from strawberry.relay import GlobalID


@strawberry.type
class LazyBook:
    id: GlobalID
    title: str
