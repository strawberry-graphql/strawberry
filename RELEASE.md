Release type: minor

This release removes support for Apollo Federation v1 and improves Federation v2 support with explicit version control and new directives.

## Breaking Changes

- **Removed support for Apollo Federation v1**: All schemas now use Federation v2
- **Removed `enable_federation_2` parameter**: Replaced with `federation_version` parameter
- Federation v2 is now always enabled with version 2.11 as the default

## Migration

### If you were using `enable_federation_2=True`

Remove the parameter:

```python
# Before
schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

# After
schema = strawberry.federation.Schema(query=Query)
```

### If you were using Federation v1

You must migrate to Federation v2. See the [breaking changes documentation](https://strawberry.rocks/docs/breaking-changes/0.285.0) for detailed migration instructions.

## New Features

- **Version control**: Specify Federation v2 versions (2.0 - 2.11):

```python
schema = strawberry.federation.Schema(
    query=Query, federation_version="2.5"  # Specify a specific version if needed
)
```

- **New directives**: Added support for `@context`, `@fromContext`, `@cost`, and `@listSize` directives (v2.7+)
- **Automatic validation**: Ensures directives are compatible with your chosen federation version
- **Improved performance**: Faster version parsing using dictionary lookups
