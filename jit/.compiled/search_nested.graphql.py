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
    arguments["first"] = variables["first"]
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
        # Query.search.author.articles
        arguments = {}
        field = root_type_3.fields[3]
        value_3 = field._resolver(value_2, None, **arguments)
        # root_value_variable: value_3
        results_4 = []
        for item in value_3:
            # root_value_variable: item
            # Object: Article
            results_5 = {}
            root_type_5 = Article.__strawberry_definition__
            # Query.search.author.articles
            # Query.search.author.articles.title
            arguments = {}
            field = root_type_5.fields[1]
            value_5 = item.title
            # root_value_variable: value_5
            results_5["title"] = value_5
            results_4["articles"] = results_5
            results_4.append(results_5)
        results_3["articles"] = results_4

        results_2["author"] = results_3
        results_1.append(results_2)
    results_0["search"] = results_1

    return results_0
