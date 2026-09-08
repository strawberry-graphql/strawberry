---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Schema directive locations and repeatability
    are now validated when schemas are created. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Schema construction now validates custom schema
    directive locations and repeatability, preventing invalid directive applications
    from being silently omitted or emitted as invalid SDL. 🍓
---

This release fixes validation of schema directive applications.

Strawberry now validates every supported type-system location during schema
construction, including the distinctions between objects and interfaces and between
output and input fields. Applying a directive outside its declared locations raises
an actionable error that identifies the directive, actual location, and schema
element.

Applying a non-repeatable directive more than once to the same schema element now
also raises an error. Repeatable directives retain their Python attachment order,
and non-repeatable directives can still be reused on separate elements. Valid
Federation applications such as multiple `@key` and `@tag` directives continue to
work.

This may expose invalid applications that Strawberry previously omitted from SDL or
printed as SDL rejected by GraphQL tools. Move or remove those applications, add the
intended location to the directive definition, or set `repeatable=True` when repeated
applications are intentional.
