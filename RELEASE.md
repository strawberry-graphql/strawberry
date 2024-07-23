Release type: patch

Update federation entity resolver exception handling to set the result to the original error instead of a `GraphQLError`, which obscured the original message and meta-fields.
