---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Malformed JSON request bodies now get a 400
    instead of a 500. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. HTTP views now reject JSON request bodies
    that aren't objects, invalid UTF-8, and malformed batch operations with a 400
    response instead of crashing with a 500.
---

This release fixes HTTP views returning a 500 error for some malformed JSON
request bodies.

The following requests now get a 400 response in all integrations:

- a JSON body that isn't an object, such as `null`, `1` or `"query"`
- a body that isn't valid UTF-8
- a batch containing an operation that isn't an object, or whose `query`,
  `variables` or `extensions` have the wrong type. Previously these operations
  skipped the checks applied to single requests.
