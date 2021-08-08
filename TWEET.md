Another great feature by @jonnykim! Now we are able to pass
custom validators when executing GraphQL queries. And we
already have one built-in validator to disable queries by depth!

Check it out here 👉 $release_url

---

This release adds a query depth limit validation rule so that you can guard
against malicious queries:

```python
validation_rules = [depth_limit_validator(2)]
result = schema.execute_sync("""
    query MyQuery {
      user {
        pets {
          owner {
              name
          }
        }
      }
    } """,
    validation_rules=validation_rules,
)
assert result.errors[0].message == "'MyQuery' exceeds maximum operation depth of 2"
```
