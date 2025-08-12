from typing import Any, Dict, List, Optional

def execute_query(root, context=None, variables=None):
    """Execute JIT-compiled GraphQL query with optimizations."""
    result = {}
    errors = []
    # Coerce variables
    from graphql.execution.values import get_variable_values
    coerced = get_variable_values(_schema, _var_defs, variables or {})
    if isinstance(coerced, list):
        for error in coerced:
            errors.append({'message': str(error), 'path': []})
        return {"data": None, "errors": errors}
    variables = coerced
    
    info = _MockInfo(_schema)
    info.root_value = root
    info.context = context
    info.variable_values = variables
    
    # Execute query with error handling
    try:
        try:
            info.field_name = "posts"
            kwargs = {}
            kwargs['limit'] = 10
            kwargs['published'] = None
            kwargs['priority'] = None
            kwargs['limit'] = (_scalar_parsers.get('Int', lambda x: x)(info.variable_values.get('limit')) if info.variable_values.get('limit') is not None else None)
            field_posts_value = _resolvers['resolver_0'](root, info, **kwargs)
            if field_posts_value is not None:
                result["posts"] = []
                for idx, item_0 in enumerate(field_posts_value):
                    item_result_0 = {}
                    try:
                        info.field_name = "id"
                        field_id_value = _resolvers['resolver_1'](item_0, info)
                        item_result_0["id"] = field_id_value
                    except Exception as e:
                        errors.append({'message': str(e), 'path': [] + ['posts'] + [idx] + ['id']})
                        raise  # Propagate non-nullable error
                    try:
                        info.field_name = "title"
                        field_title_value = _resolvers['resolver_2'](item_0, info)
                        item_result_0["title"] = field_title_value
                    except Exception as e:
                        errors.append({'message': str(e), 'path': [] + ['posts'] + [idx] + ['title']})
                        raise  # Propagate non-nullable error
                    try:
                        info.field_name = "published"
                        field_published_value = _resolvers['resolver_3'](item_0, info)
                        item_result_0["published"] = field_published_value
                    except Exception as e:
                        errors.append({'message': str(e), 'path': [] + ['posts'] + [idx] + ['published']})
                        raise  # Propagate non-nullable error
                    result["posts"].append(item_result_0)
            else:
                result["posts"] = None
        except Exception as e:
            errors.append({'message': str(e), 'path': [] + ['posts']})
            raise  # Propagate non-nullable error
    except Exception as root_error:
        if not any(e.get('message') == str(root_error) for e in errors):
            errors.append({'message': str(root_error), 'path': []})
        result = None
    
    # Return result with errors if any
    if errors:
        return {"data": result, "errors": errors}
    return result