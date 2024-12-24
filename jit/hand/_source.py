# TODO: variables
async def _compiled_operation(schema, root_value, variables):
    results_0 = {}
    root_type_0 = Query.__strawberry_definition__
    # Query
    # Query.search
    arguments = {}
    arguments["query"] = variables["query"]
    arguments["first"] = 10
    field = root_type_0.fields[0]
    value = await field._resolver(root_value, None, **arguments)
    results_1 = []
    for item in value:
        results_2 = {}
        root_type_2 = Article.__strawberry_definition__
        # Query.search
        # Query.search.title
        arguments = {}
        field = root_type_2.fields[1]
        value = item.title
        results_2["title"] = value
        results_1.append(results_2)
    results_0["search"] = results_1

    return results_0
