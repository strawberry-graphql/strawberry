Release type: patch

Introduces an optional operation_extensions parameter throughout the GraphQL
execution flow—adding it to execution entry points and embedding it into the
ExecutionContext—so custom extensions can access per-operation metadata.
