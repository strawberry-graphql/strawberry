
import pytest

from starlette.testclient import TestClient

import strawberry
from strawberry.types import Info
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

def test_with_context_getter():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get('request') != None
            assert info.context.get('strawberry') == 'rocks'
            return "abc"
    
    def get_context():
        return {"strawberry": "rocks"}
    
    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, context_getter=get_context, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})
    
    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}
    
def test_without_context_getter():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get('request') != None
            assert info.context.get('strawberry') == None
            return "abc"
    
    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})
    
    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}
