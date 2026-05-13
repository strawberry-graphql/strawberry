Release type: patch

The `types.field.resolver.ReservedParameterSpecification` protocol now requires classes to have `__hash__` as well,
because instances of those classes are to be used as dictionary keys.
