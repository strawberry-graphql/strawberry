Release type: minor

This release adds a query depth limit validation rule so that you can guard
against malicious queries:

```python
import strawberry
from strawberry.schema import default_validation_rules
from strawberry.tools import depth_limit_validator


# Add the depth limit validator to the list of default validation rules
validation_rules = (
  default_validation_rules + [depth_limit_validator(3)]
)

result = schema.execute_sync(
    """
    query MyQuery {
      user {
        pets {
          owner {
            pets {
              name
            }
          }
        }
      }
    }
    """,
    validation_rules=validation_rules,
  )
)
assert len(result.errors) == 1
assert result.errors[0].message == "'MyQuery' exceeds maximum operation depth of 3"
```
