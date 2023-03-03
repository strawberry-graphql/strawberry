---
title: Supported schemas
---

# Supported schemas

Supported schemas is an optional feature that enable you to annotate a field and
only make it available for a specific set of schema and/or versions.

## Motivations

### Running multiple version of the API

While GraphQL APIs are usually not versioned and should strive to never introduce
breaking changes, the fact is that you may want to version your GraphQL API and
run multiple versions in parallel within the same server.

Instead of duplicating code or creating a complex class hierarchy, `supported_schemas`
enable you to annotate a field and specify in which version this field should be
available.

### Running multiple schemas using "similar" objects

Sometimes, you may want to serve multiple GraphQL APIs that use the same objects
but with slightly different fields. A good example is that your third party GraphQL 
API might expose the "core" fields of an object but your first party API might 
add more information and more fields for your first party apps.

Instead of duplicating code or creating a complex class hierarchy, `supported_schemas`
enable you to annotate a field and specify in which schemas those fields should
be available.

## How it works

You can anotate a field using the `supported_schemas` argument:

```python
import strawberry
from strawberry.field import SupportedSchema

@strawberry.type
class User:
    # [...]

    @strawberry.field(name="debugMessage", supported_schemas=[
        SupportedSchema(name="internal"),
    ])
    def get_debug_message(self) -> str:
        # This field will only appear in the schemas called `internal`
        # [...]

    @strawberry.field(name="riskScore", supported_schemas=[
        SupportedSchema(name="internal", until_version="1.2"),
    ])
    def get_old_risk_score(self) -> float:
        # This field will only appear in the schemas called `internal` that have
        # a version lower than or equal to `1.2`
        # [...]

    @strawberry.field(name="riskScore", supported_schemas=[
        SupportedSchema(name="internal", from_version="1.3"),
    ])
    def get_new_risk_score(self) -> float:
        # This field will only appear in the schemas called `internal` that have
        # a version higher than or equal to `1.3`
        # [...])
```

When instantiating your schema, you can specify a name and version, which will
be used during the schema generation to filter the fields accordingly:

```python
import strawberry
from strawberry.schema.identifier import SchemaIdentifier

# [...] Define `Query` and `Mutation`

internal_schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    schema_identifier=SchemaIdentifier(name="internal", version="1.4"),
)
```

## Advanced usage

By default, versions are compared via basic string comparison. If your versioning
scheme is complex, you can use a custom version comparator:

```python
def custom_comparator(version1: str, version2: str) -> int:
    # Should return 0 if `version1` and `version2` are equal
    # Should return a negative integer (usually -1) if `version1` < `version2`
    # Should return a positive integer (usually 1) if `version1` > `version2`

SchemaIdentifier(
    name="internal",
    version="1.4",
    version_comparator=custom_comparator
),
```