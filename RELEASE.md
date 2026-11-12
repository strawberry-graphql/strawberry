---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Malformed multipart upload requests now get
    a 400 instead of a 500. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Multipart file upload requests with a
    malformed `operations` or `map` field are now rejected with a clear 400
    response instead of crashing with a 500.
---

This release fixes multipart file upload requests with a malformed `operations`
or `map` field returning a 500 error.

These requests now get a 400 response describing the problem, for example when
`operations` isn't a JSON object or an array of objects, `map` isn't a JSON
object, a `map` value isn't an array of strings, or a path in `map` is invalid:
it uses a non-numeric or negative list index, an index out of range, a key that
doesn't exist, or goes into a non-container value.
