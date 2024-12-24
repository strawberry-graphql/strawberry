# TODO: variables
async def _compiled_operation(schema, root_value, variables):
    # root_value_variable: root_value
    # Object: Query
    results_0 = {}
    root_type_0 = Query.__strawberry_definition__
    # Query
    # Query.search
    arguments = {}
    arguments["query"] = variables["query"]
    arguments["first"] = 10000
    field = root_type_0.fields[0]
    value_0 = await field._resolver(root_value, None, **arguments)
    # root_value_variable: value_0
    results_1 = []
    for item in value_0:
        # root_value_variable: item
        # Object: Article
        results_2 = {}
        root_type_2 = Article.__strawberry_definition__
        # Query.search
        # Query.search.id
        arguments = {}
        field = root_type_2.fields[0]
        value_2 = item.id
        # root_value_variable: value_2
        results_2["id"] = value_2
        # Query.search.title
        arguments = {}
        field = root_type_2.fields[1]
        value_2 = item.title
        # root_value_variable: value_2
        results_2["title"] = value_2
        # Query.search.author
        arguments = {}
        field = root_type_2.fields[2]
        value_2 = item.author
        # root_value_variable: value_2
        # Object: User
        results_3 = {}
        root_type_3 = User.__strawberry_definition__
        # Query.search.author
        # Query.search.author.name
        arguments = {}
        field = root_type_3.fields[1]
        value_3 = value_2.name
        # root_value_variable: value_3
        results_3["name"] = value_3
        results_2["author"] = results_3
        results_1["search"] = results_2
        results_1.append(results_2)
    results_0["search"] = results_1

    return results_0
