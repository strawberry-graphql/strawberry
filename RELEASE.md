Release type: minor

This release adds a new method `get_fields` on the `Schema` class.
You can use `get_fields` to hide certain field based on some conditions,
for example:

```python
@strawberry.type
class User:
    name: str
    email: str = strawberry.field(metadata={"tags": ["internal"]})


@strawberry.type
class Query:
    user: User


def public_field_filter(field: StrawberryField) -> bool:
    return "internal" not in field.metadata.get("tags", [])


class PublicSchema(strawberry.Schema):
    def get_fields(
        self, type_definition: StrawberryObjectDefinition
    ) -> List[StrawberryField]:
        return list(filter(public_field_filter, type_definition.fields))


schema = PublicSchema(query=Query)
```

The schema here would only have the `name` field on the `User` type.
