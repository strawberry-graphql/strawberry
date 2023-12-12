import strawberry

from strawberry.schema.hash import hash256, is_valid_hash256
from graphql.error.syntax_error import GraphQLSyntaxError

from strawberry.schema.config import StrawberryConfig

from strawberry.schema.apq.constants import QUERY_HASH_NOT_FOUND_ERROR
    
def test_hash():
    query = """{ helloWorld }"""
    result = hash256(query)
    assert hash256(query) == result
    
def test_valid_hash():
    result = hash256("""{ helloWorld }""")
    assert is_valid_hash256(result)

    
def test_simple_query_syntax_error():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello_world(self) -> str:
            return "hi"
    
    schema = strawberry.Schema(query=Query, config=StrawberryConfig(use_apq=False))
    
    query = """{
        helloWorld
    }"""
    hashed_query  = hash256(query)
    
    result = schema.execute_sync(hashed_query)
    
    assert result.errors != []
    assert isinstance(result.errors[0], GraphQLSyntaxError)
    
def test_simple_query_notfound():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello_world(self) -> str:
            return "hi"
    
    schema = strawberry.Schema(query=Query, config=StrawberryConfig(use_apq=True))
    
    query = """{
        helloWorld
    }"""
    hashed_query  = hash256(query)
    
    result = schema.execute_sync(hashed_query)
    
    assert result.errors != []
    assert result.errors[0].message == QUERY_HASH_NOT_FOUND_ERROR