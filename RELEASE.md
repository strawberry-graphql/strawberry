---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes validation of the
    `Upload` scalar, so non-file values are rejected before your resolver runs.
    🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes validation of the
    `Upload` scalar. Sending a string, number or object where a file is expected
    now fails validation with a clear error instead of reaching your resolver.
---

This release fixes validation of the `Upload` scalar.

Previously the `Upload` scalar accepted any value, so a client could send a
plain JSON value where a file was expected and the resolver would run with it,
usually failing later with a confusing internal error:

```graphql
mutation {
  readFile(file: "not a file")
}
```

Files can only be provided through a multipart request, so `Upload` will now
reject values that come from the JSON body of the request, whether they are
passed as variables or inline literals, including inside input types and lists:

```json
{
  "errors": [
    {
      "message": "Upload cannot represent a non-file value: 'not a file'"
    }
  ]
}
```

The file objects provided by every integration are still accepted, and nullable
`Upload` fields still accept `null`.
