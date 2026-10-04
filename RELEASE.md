---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Importing Strawberry no longer imports
    pydantic, so apps start faster when pydantic is installed, and a broken
    pydantic install no longer stops Strawberry from importing.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Importing Strawberry no longer imports
    pydantic: the experimental pydantic integration is now loaded the first time
    it's used. Apps that have pydantic installed but don't use the integration
    start faster, and Strawberry stays importable even when the installed
    pydantic is broken.
---

This release fixes `import strawberry` importing pydantic whenever it's
installed, which slowed down the startup of every app, including the ones that
don't use pydantic, and made Strawberry impossible to import when the installed
pydantic was broken.

The experimental pydantic integration is now imported the first time it's
used, and `PydanticErrorExtension` no longer imports pydantic. With pydantic
installed, importing Strawberry now loads about 60 fewer modules.

`strawberry.experimental.pydantic` keeps working the same way, whether it's
imported with `import strawberry.experimental.pydantic`, with
`from strawberry.experimental import pydantic`, or accessed as an attribute of
`strawberry.experimental`.
