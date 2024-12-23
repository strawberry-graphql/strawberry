import asyncio

from jit.test import Article, Query, User

import strawberry


# TODO: variables
async def _compiled_operation(schema, root_value):
    results_0 = {}
    root_type = Query.__strawberry_definition__
    # Query
    # Query.users
    field = root_type.fields[0]
    breakpoint()
    value = await field._resolver(root_value, None)
    results_1 = []
    for item in value:
        results_2 = {}
        root_type = User.__strawberry_definition__
        # Query.users
        # Query.users.id
        field = root_type.fields[0]
        value = field._resolver(item, None)
        results_2["id"] = value
        # Query.users.name
        field = root_type.fields[1]
        value = field._resolver(item, None)
        results_2["name"] = value
        results_1.append(results_2)
    results_0["users"] = results_1

    # Query.articles
    field = root_type.fields[1]
    value = await field._resolver(root_value, None)
    results_1 = []
    for item in value:
        results_2 = {}
        root_type = Article.__strawberry_definition__
        # Query.articles
        # Query.articles.id
        field = root_type.fields[0]
        value = field._resolver(item, None)
        results_2["id"] = value
        # Query.articles.title
        field = root_type.fields[1]
        value = field._resolver(item, None)
        results_2["title"] = value
        results_1.append(results_2)
    results_0["articles"] = results_1

    return results_0


schema = strawberry.Schema(Query)

asyncio.run(_compiled_operation(schema, None))
