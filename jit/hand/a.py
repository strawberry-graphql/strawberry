import strawberry
from jit.test import Article, Query, User

schema = strawberry.Schema(Query)


# TODO: variables
async def _compiled_operation(schema, root_value={}):
    results_0 = {}
    root_type_0 = Query.__strawberry_definition__

    field = root_type_0.fields[0]
    value = await field._resolver(root_value, None)
    results_1 = []
    root_type_2 = User.__strawberry_definition__

    for item in value:
        results_2 = {
            "id": item.id,
            "name": item.name,
        }
        field = root_type_2.fields[2]

        value = await field._resolver(item, None)
        results_3 = []

        for item in value:
            results_3.append({"id": item.id, "title": item.title})
        results_2["articles"] = results_3

        results_1.append(results_2)
    results_0["users"] = results_1

    # Query.articles
    field = root_type_0.fields[1]
    value = await field._resolver(root_value, None)
    results_1 = []
    root_type_2 = Article.__strawberry_definition__
    for item in value:
        results_1.append({"id": item.id, "title": item.title})
    results_0["articles"] = results_1

    return results_0
