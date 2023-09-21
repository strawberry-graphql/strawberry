Release type: patch

This release fixes an issue when trying to generate code from a schema that
was using double quotes inside descriptions.

The following schema will now generate code correctly:

```graphql
"""
A type of person or character within the "Star Wars" Universe.
"""
type Species {
  """
  The classification of this species, such as "mammal" or "reptile".
  """
  classification: String!
}
```
