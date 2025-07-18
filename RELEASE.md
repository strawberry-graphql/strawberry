Release type: patch

This release renames the `ExecutionContext.errors` attribute to `ExecutionContext.pre_execution_errors` to better reflect its purpose. The old `errors` attribute is now deprecated but still available for backward compatibility.

The `pre_execution_errors` attribute specifically stores errors that occur during the pre-execution phase (parsing and validation), making the distinction clearer from errors that might occur during the actual execution phase.

For backward compatibility, accessing `ExecutionContext.errors` will now emit a deprecation warning and return the value of `pre_execution_errors`.
