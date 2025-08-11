#!/usr/bin/env python
"""
Standalone JIT-compiled GraphQL executor.
This file was automatically generated and can be executed independently.

Query Details:
- Operation: query HelloWorld
- Root Type: Query
- Top-level Fields: hello
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
    info.field_name = "hello"
    info.parent_type = "Query"
    kwargs = {}
    kwargs['name'] = 'world'
    kwargs['name'] = 'GraphQL'
    resolver = _resolvers['resolver_0']
    field_hello_value = await resolver(root, info, **kwargs)
    result["hello"] = field_hello_value
    return result


# Initialize resolvers for standalone execution
_resolvers['resolver_0'] = _default_resolver  # Custom resolver in actual execution


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
