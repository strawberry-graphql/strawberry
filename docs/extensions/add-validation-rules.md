---
title: Add Validation Rules
summary: Add GraphQL validation rules.
tags: validation,security
---

# `AddValidationRules`

This extension allows you add custom validation rules.

See
[graphql.validation.rules.custom](https://github.com/graphql-python/graphql-core/tree/main/src/graphql/validation/rules/custom)
for some custom rules that can be added from GraphQl-core.

## Usage example:

```python
import strawberry
from strawberry.extensions import AddValidationRules
from graphql import ValidationRule


class MyCustomRule(ValidationRule): ...


schema = strawberry.Schema(
    Query,
    extensions=[
        AddValidationRules(MyCustomRule),
    ],
)
```

## API reference:

```python
class AddValidationRules(validation_rules): ...
```

#### `validation_rules: List[Type[ASTValidationRule]]`

List of GraphQL validation rules.

## More examples:

<details>
  <summary>Adding a custom rule</summary>

```python
import strawberry
from strawberry.extensions import AddValidationRules
from graphql import ValidationRule


class CustomRule(ValidationRule):
    def enter_field(self, node, *args) -> None:
        if node.name.value == "example":
            self.report_error(GraphQLError("Can't query field 'example'"))


schema = strawberry.Schema(
    Query,
    extensions=[
        AddValidationRules([CustomRule]),
    ],
)

result = schema.execute_sync("{ example }")

assert str(result.errors[0]) == "Can't query field 'example'"
```

</details>

<details>
  <summary>Adding the `NoDeprecatedCustomRule` from GraphQL-core</summary>

```python
import strawberry
from strawberry.extensions import AddValidationRules
from graphql.validation import NoDeprecatedCustomRule

schema = strawberry.Schema(
    Query,
    extensions=[
        AddValidationRules([NoDeprecatedCustomRule]),
    ],
)
```

</details>

<details>
  <summary>Adding the `NoSchemaIntrospectionCustomRule` from GraphQL-core</summary>

```python
import strawberry
from strawberry.extensions import AddValidationRules
from graphql.validation import NoSchemaIntrospectionCustomRule

schema = strawberry.Schema(
    Query,
    extensions=[
        AddValidationRules([NoSchemaIntrospectionCustomRule]),
    ],
)
```

</details>
