import strawberry

from strawberry.schema.hash import hash256, is_valid_hash256
from graphql.error.syntax_error import GraphQLSyntaxError
    
def test_hash():
    query = """{ helloWorld }"""
    result = hash256(query)
    assert hash256(query) == result
    
def test_valid_hash():
    result = hash256("""{ helloWorld }""")
    assert is_valid_hash256(result)

    
def test_simple_query_notfound():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello_world(self) -> str:
            return "hi"
    
    schema = strawberry.Schema(query=Query)
    
    query = """{
        helloWorld
    }"""
    hashed_query  = hash256(query)
    
    result = schema.execute_sync(hashed_query)
    
    assert result.errors != []
    assert isinstance(result.errors[0], GraphQLSyntaxError)