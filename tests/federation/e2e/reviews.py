import typing

import strawberry
import uvicorn
from starlette.applications import Starlette
from strawberry.asgi import GraphQL


@strawberry.federation.type(keys=["id"])
class Review:
    id: strawberry.ID
    body: str


REVIEWS_PER_PRODUCT = {
    "ABC123": [Review(strawberry.ID("1"), "Awesome product!")],
    "DEF456": [Review(strawberry.ID("2"), "Not really enjoying it.")],
}


@strawberry.federation.type(extend=True, keys=["upc"])
class Product:
    upc: str = strawberry.federation.field(external=True)

    @strawberry.field
    def reviews(self, info) -> typing.List[Review]:
        return REVIEWS_PER_PRODUCT.get(self.upc, [])

    @classmethod
    def resolve_reference(cls, upc):
        return Product(upc=upc)


@strawberry.federation.type
class Query:
    ...


schema = strawberry.federation.Schema(Query, types=[Review, Product])

app = Starlette(debug=False)
app.add_route("/graphql", GraphQL(schema))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4002, access_log=False)
