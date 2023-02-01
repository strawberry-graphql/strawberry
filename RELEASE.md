Release type: patch

This patch introduces the `FieldAttributesRule` to the `QueryDepthLimiter` extension that provides
a more verbose way of specifying the rules by which a query's depth should be limited.

These can be any or all of the field name, the field arguments, and the field keys. Multiple
rules can be specified that will be evaluated independently to yield the final fully limited query.

For example,
the following query:
```python
"""
    query {
      matt: user(name: "matt") {
        email
      }
      andy: user(name: "andy") {
        email
        address {
          city
        }
        pets {
          name
          owner {
            name
          }
        }
      }
    }
"""
```
can have its depth limited by the following `FieldAttributesRule`:
```python
FieldAttributesRule(
    field_name=user,
    field_arguments={ "name": "matt" },
    field_keys=address,
)
```
so that it *effectively* becomes:
```python
"""
    query {
      andy: user(name: "andy") {
        email
        pets {
          name
          owner {
            name
          }
        }
      }
    }
"""
```