import strawberry

from strawberry.schema.hash import hash256, is_valid_hash256
from graphql.error.syntax_error import GraphQLSyntaxError

from strawberry.schema.config import StrawberryConfig

from strawberry.schema.apq.constants import QUERY_HASH_NOT_FOUND_ERROR

from strawberry.schema.apq.apq_extension import APQExtension
    
def test_hash():
    query = """{ helloWorld }"""
    result = hash256(query)
    assert hash256(query) == result
    
def test_valid_hash():
    result = hash256("""{ helloWorld }""")
    assert is_valid_hash256(result)

    
def test_simple_query_syntax_error(simple_schema: strawberry.Schema):
    query = """{
        helloWorld
    }"""
    hashed_query  = hash256(query)
    
    result = simple_schema.execute_hashed_sync(hashed_query)
    
    assert result.errors != []
    assert isinstance(result.errors[0], GraphQLSyntaxError)
    
def test_simple_query_notfound(simple_schema: strawberry.Schema):
    query = """{
        helloWorld
    }"""
    hashed_query  = hash256(query)
    
    result = simple_schema.execute_hashed_sync(hashed_query)
    
    assert result.errors != []
    assert result.errors[0].message == QUERY_HASH_NOT_FOUND_ERROR
    
def test_simple_query_extension_no_query(simple_schema: strawberry.Schema):    
    query = """{
        helloWorld
    }"""
    hashed_query  = hash256(query)
    
    result = simple_schema.execute_hashed_sync(hashed_query)
    
    assert result.errors != []
    assert result.errors[0].message == QUERY_HASH_NOT_FOUND_ERROR
    


def __hash_and_validate_query(schema: strawberry.Schema, query: str):
    hashed_query  = hash256(query)
    
    result = schema.execute_hashed_sync(hashed_query)
    assert result.errors != []
    assert result.errors[0].message == QUERY_HASH_NOT_FOUND_ERROR
    
    schema.cache_hashed_query(hashed_query, query)
    
    return hashed_query

def test_simple_query_extension_no_query_sendback(simple_schema: strawberry.Schema):
    query = """{
        helloWorld
    }"""
    hashed_query = __hash_and_validate_query(simple_schema, query)
    
    result = simple_schema.execute_hashed_sync(hashed_query)
    assert result.data['helloWorld'] == 'hi'