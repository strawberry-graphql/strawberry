---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Invalid relay GlobalIDs and null values for
    Maybe fields are now reported as StrawberryInputCoercionError, so error
    masking can tell them apart from server errors.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Invalid relay GlobalIDs and null values for
    strawberry.Maybe fields and arguments that don't accept null are now
    reported as StrawberryInputCoercionError, like other invalid client input,
    so error handling such as MaskErrors can keep showing them to clients.
---

This release fixes some errors in client input not being reported as
`StrawberryInputCoercionError`, the exception Strawberry uses for invalid input
values, so that error handling, like `MaskErrors`, can tell them apart from
server errors:

- `null` for a `strawberry.Maybe` field or argument that doesn't accept it,
  whether it's sent in the query or in variables;
- a relay `GlobalID` that can't be parsed, which raises the new
  `strawberry.relay.InvalidGlobalIDError`. It's also a `GlobalIDValueError`, so
  code that handles that keeps working, and its message is now
  `Value cannot represent a GlobalID: "...".`, like the built-in scalars,
  instead of the base64 or UTF-8 decoding error.

The other messages are unchanged. As these errors are now `GraphQLError`s,
exception handlers registered for `StrawberryGraphQLError` or `GraphQLError`
also handle invalid `GlobalID` arguments, like other input errors.
