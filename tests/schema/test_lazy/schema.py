import strawberry
from tests.schema.test_lazy.type_c import Query

schema = strawberry.Schema(query=Query)
