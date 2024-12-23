# TODO: variables
async def _compiled_operation(schema, root_value):
    results_0 = {}
    root_type_0 = Query.__strawberry_definition__
    # Query
    # Query.users
    field = root_type_0.fields[0]
    value = await field._resolver(root_value, None)
    results_1 = []
    for item in value:
        results_2 = {}
        root_type_2 = User.__strawberry_definition__
        # Query.users
        # Query.users.id
        field = root_type_2.fields[0]
        value = item.id
        results_2["id"] = value
        # Query.users.name
        field = root_type_2.fields[1]
        value = item.name
        results_2["name"] = value
        # Query.users.articles
        field = root_type_2.fields[2]
        value = await field._resolver(item, None)
        results_3 = []
        for item in value:
            results_4 = {}
            root_type_4 = Article.__strawberry_definition__
            # Query.users.articles
            # Query.users.articles.id
            field = root_type_4.fields[0]
            value = item.id
            results_4["id"] = value
            # Query.users.articles.title
            field = root_type_4.fields[1]
            value = item.title
            results_4["title"] = value
            results_3.append(results_4)
        results_2["articles"] = results_3

        results_1.append(results_2)
    results_0["users"] = results_1

    # Query.articles
    field = root_type_0.fields[1]
    value = await field._resolver(root_value, None)
    results_1 = []
    for item in value:
        results_2 = {}
        root_type_2 = Article.__strawberry_definition__
        # Query.articles
        # Query.articles.id
        field = root_type_2.fields[0]
        value = item.id
        results_2["id"] = value
        # Query.articles.title
        field = root_type_2.fields[1]
        value = item.title
        results_2["title"] = value
        results_1.append(results_2)
    results_0["articles"] = results_1

    return results_0
