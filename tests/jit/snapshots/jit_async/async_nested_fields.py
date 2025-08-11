#!/usr/bin/env python
"""
Standalone JIT-compiled GraphQL executor.
This file was automatically generated and can be executed independently.

Query Details:
- Operation: query GetPosts
- Root Type: Query
- Top-level Fields: posts
- Generated: [timestamp]
"""

from typing import Any, Dict, List, Optional
class _MockInfo:
    """Mock GraphQLResolveInfo for JIT execution."""
    def __init__(self, schema):
        self.schema = schema
        self.field_name = None
        self.parent_type = None
        self.return_type = None
        self.path = []
        self.operation = None
        self.variable_values = {}
        self.context = None
        self.root_value = None
        self.fragments = {}


def _default_resolver(obj, info):
    """Default field resolver that gets attributes or dict values."""
    field_name = info.field_name
    if hasattr(obj, field_name):
        return getattr(obj, field_name)
    elif isinstance(obj, dict):
        return obj.get(field_name)
    return None


# Resolver map - will be populated with actual resolvers at runtime
# For standalone execution, these will use the default resolver
_resolvers = {}


import asyncio
import inspect

async def execute_query(root, context=None, variables=None):
    """Execute the JIT-compiled GraphQL query."""
    result = {}
    info = _MockInfo(None)  # Mock info object
    info.root_value = root
    info.context = context
    info.variable_values = variables or {}
    info.field_name = "posts"
    info.parent_type = "Query"
    kwargs = {}
    kwargs['limit'] = 10
    kwargs['limit'] = 2
    resolver = _resolvers['resolver_0']
    field_posts_value = await resolver(root, info, **kwargs)
    if field_posts_value is not None:
        if isinstance(field_posts_value, list):
            result["posts"] = []
            for item_posts in field_posts_value:
                item_posts_result = {}
                info.field_name = "id"
                info.parent_type = "Post"
                resolver = _resolvers['resolver_1']
                field_id_value = resolver(item_posts, info)
                item_posts_result["id"] = field_id_value
                info.field_name = "title"
                info.parent_type = "Post"
                resolver = _resolvers['resolver_2']
                field_title_value = resolver(item_posts, info)
                item_posts_result["title"] = field_title_value
                info.field_name = "author"
                info.parent_type = "Post"
                resolver = _resolvers['resolver_3']
                field_author_value = await resolver(item_posts, info)
                if field_author_value is not None:
                    nested_author_result = {}
                    info.field_name = "name"
                    info.parent_type = "Author"
                    resolver = _resolvers['resolver_4']
                    field_name_value = resolver(field_author_value, info)
                    nested_author_result["name"] = field_name_value
                    info.field_name = "bio"
                    info.parent_type = "Author"
                    kwargs = {}
                    kwargs['delay'] = 0
                    resolver = _resolvers['resolver_5']
                    field_bio_value = await resolver(field_author_value, info, **kwargs)
                    nested_author_result["bio"] = field_bio_value
                    item_posts_result["author"] = nested_author_result
                else:
                    item_posts_result["author"] = None
                info.field_name = "viewCount"
                info.parent_type = "Post"
                resolver = _resolvers['resolver_6']
                field_viewCount_value = await resolver(item_posts, info)
                item_posts_result["viewCount"] = field_viewCount_value
                result["posts"].append(item_posts_result)
        else:
            single_item_result = {}
            info.field_name = "id"
            info.parent_type = "Post"
            resolver = _resolvers['resolver_7']
            field_id_value = resolver(field_posts_value, info)
            single_item_result["id"] = field_id_value
            info.field_name = "title"
            info.parent_type = "Post"
            resolver = _resolvers['resolver_8']
            field_title_value = resolver(field_posts_value, info)
            single_item_result["title"] = field_title_value
            info.field_name = "author"
            info.parent_type = "Post"
            resolver = _resolvers['resolver_9']
            field_author_value = await resolver(field_posts_value, info)
            if field_author_value is not None:
                nested_author_result = {}
                info.field_name = "name"
                info.parent_type = "Author"
                resolver = _resolvers['resolver_10']
                field_name_value = resolver(field_author_value, info)
                nested_author_result["name"] = field_name_value
                info.field_name = "bio"
                info.parent_type = "Author"
                kwargs = {}
                kwargs['delay'] = 0
                resolver = _resolvers['resolver_11']
                field_bio_value = await resolver(field_author_value, info, **kwargs)
                nested_author_result["bio"] = field_bio_value
                single_item_result["author"] = nested_author_result
            else:
                single_item_result["author"] = None
            info.field_name = "viewCount"
            info.parent_type = "Post"
            resolver = _resolvers['resolver_12']
            field_viewCount_value = await resolver(field_posts_value, info)
            single_item_result["viewCount"] = field_viewCount_value
            result["posts"] = single_item_result
    else:
        result["posts"] = None
    return result


# Initialize resolvers for standalone execution
_resolvers['resolver_0'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_1'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_2'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_3'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_4'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_5'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_6'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_7'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_8'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_9'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_10'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_11'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_12'] = _default_resolver  # Custom resolver in actual execution


if __name__ == '__main__':
    # Example usage when run standalone
    print('This is a JIT-compiled GraphQL executor.')
    print('To use it, import and call execute_query() with your root object.')
    print()
    print('Example:')
    print('  from this_file import execute_query')
    print('  result = execute_query(root_object)')
    print('  print(result)')

    # Demo with sample data
    class SampleObject:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    # You can test with your own data structure here
    # sample_root = SampleObject(...)
    # result = execute_query(sample_root)
    # print(result)
