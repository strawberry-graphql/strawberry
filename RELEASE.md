Release type: patch

We added better messaging for users of this library regarding the use of
non-strawberry types in Unions.
We include an example stack trace below.


Here's the stack trace resulting from a scalar getting included in a Union:
```
  File "/Users/macadmin/.local/share/virtualenvs/strawberry-QhDFl6sY/lib/python3.8/site-packages/graphql/type/definition.py", line 799, in fields
    fields = resolve_thunk(self._fields)
  File "/Users/macadmin/.local/share/virtualenvs/strawberry-QhDFl6sY/lib/python3.8/site-packages/graphql/type/definition.py", line 299, in resolve_thunk
    return thunk() if callable(thunk) else thunk
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/schema_converter.py", line 325, in <lambda>
    fields=lambda: self.get_graphql_fields(object_type),
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/schema_converter.py", line 228, in get_graphql_fields
    return self._get_thunk_mapping(
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/schema_converter.py", line 222, in _get_thunk_mapping
    thunk_mapping[name_converter(f)] = field_converter(f)
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/schema_converter.py", line 156, in from_field
    field_type = cast(GraphQLOutputType, self.from_maybe_optional(field.type))
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/schema_converter.py", line 474, in from_maybe_optional
    return self.from_type(type_.of_type)
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/schema_converter.py", line 479, in from_type
    if compat.is_generic(type_):
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/compat.py", line 60, in is_generic
    return type_.is_generic
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/union.py", line 104, in is_generic
    return len(self.type_params) > 0
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/union.py", line 99, in type_params
    set(itertools.chain(*(_get_type_params(type_) for type_ in self.types)))
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/union.py", line 99, in <genexpr>
    set(itertools.chain(*(_get_type_params(type_) for type_ in self.types)))
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/union.py", line 91, in _get_type_params
    raise InvalidUnionType(
strawberry.exceptions.InvalidUnionType: Type `int` cannot be used in a GraphQL Union

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/tests/schema/test_union.py", line 159, in test_cannot_use_scalars_in_the_union
    strawberry.Schema(query=Query)
  File "/Users/macadmin/Documents/GitHubProjects/strawberry/strawberry/schema/schema.py", line 99, in __init__
    self._schema = GraphQLSchema(
  File "/Users/macadmin/.local/share/virtualenvs/strawberry-QhDFl6sY/lib/python3.8/site-packages/graphql/type/schema.py", line 224, in __init__
    collect_referenced_types(query)
  File "/Users/macadmin/.local/share/virtualenvs/strawberry-QhDFl6sY/lib/python3.8/site-packages/graphql/type/schema.py", line 433, in collect_referenced_types
    collect_referenced_types(field.type)
  File "/Users/macadmin/.local/share/virtualenvs/strawberry-QhDFl6sY/lib/python3.8/site-packages/graphql/type/schema.py", line 432, in collect_referenced_types
    for field in named_type.fields.values():
  File "/usr/local/opt/python@3.8/Frameworks/Python.framework/Versions/3.8/lib/python3.8/functools.py", line 967, in __get__
    val = self.func(instance)
  File "/Users/macadmin/.local/share/virtualenvs/strawberry-QhDFl6sY/lib/python3.8/site-packages/graphql/type/definition.py", line 802, in fields
    raise cls(f"{self.name} fields cannot be resolved. {error}") from error
TypeError: Transaction fields cannot be resolved. Type `int` cannot be used in a GraphQL Union
```

Note that the output shows two stack traces.
The first stack trace yields an _InvalidUnionType_ exception:
```
strawberry.exceptions.InvalidUnionType: Type `int` cannot be used in a GraphQL Union
```

We think this gets swallowed during the schema-creation, and results in the following
message:
```
TypeError: Transaction fields cannot be resolved. Type `int` cannot be used in a GraphQL Union
```

Note that the message gets carried through, which we think is more helpful to the user.

We could not follow where the InvalidUnionType exception was swallowed.
