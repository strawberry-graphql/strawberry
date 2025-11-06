Release type: minor

This release updates the default Apollo Federation version from None to 2.11 (the latest supported version) and improves the federation version handling API.

## Changes

- **Default federation version**: Federation schemas now default to version 2.11 instead of requiring manual version specification
- **Simplified API**: The `federation_version` parameter is no longer optional, removing the need for conditional logic
- **Improved version parsing**: Version parsing is now a dictionary lookup for better performance and validation
- **Cleaner codebase**: Removed redundant code and improved type annotations

All existing federation schemas will continue to work without changes, but will now use v2.11 by default. If you need a specific version, you can still specify it:

```python
schema = strawberry.federation.Schema(
    query=Query, federation_version="2.5"  # Specify a specific version if needed
)
```

Supported versions: 2.0 - 2.11
