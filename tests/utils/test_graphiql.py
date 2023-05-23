import json

from strawberry.utils.graphiql import get_graphiql_html, DEFAULT_EXAMPLE_QUERY


def test_get_graphiql_html_with_default_example_query():
    document = get_graphiql_html()
    assert json.dumps(DEFAULT_EXAMPLE_QUERY) in document


def test_get_graphiql_html_with_new_example_query():
    NEW_EXAMPLE_QUERY = '''# Welcome to Strawberry 🍓 GraphQL API
#
# The Strawberry 🍓 GraphQL API is where fruits come true
#
'''
    document = get_graphiql_html(example_query=NEW_EXAMPLE_QUERY)
    assert json.dumps(NEW_EXAMPLE_QUERY) in document
