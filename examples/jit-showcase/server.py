"""FastAPI server with Strawberry GraphQL - JIT showcase example."""

from fastapi import FastAPI

from schema import schema
from strawberry.fastapi import GraphQLRouter

# Create FastAPI app
app = FastAPI(
    title="Strawberry GraphQL API",
    description="GraphQL API powered by Strawberry",
)

# Add GraphQL router
graphql_router = GraphQLRouter(schema)
app.include_router(graphql_router, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint with information."""
    return {
        "message": "Strawberry GraphQL API",
        "endpoints": {
            "graphql": "/graphql",
            "playground": "/graphql",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
