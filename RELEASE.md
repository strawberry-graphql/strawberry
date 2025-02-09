Release type: minor

This release refactors some of the internal execution logic by:

1. Moving execution logic from separate files into schema.py for better organization
2. Using graphql-core's parse and validate functions directly instead of wrapping them
3. Removing redundant execute.py and subscribe.py files

This is an internal refactor that should not affect the public API or functionality. The changes make the codebase simpler and easier to maintain.
