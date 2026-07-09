---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Fixes false "Unexpected argument" errors in PyCharm for @strawberry.type and @strawberry.input classes. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This patch fixes a PyCharm issue where classes decorated with @strawberry.type and @strawberry.input incorrectly showed "Unexpected argument" errors on their generated keyword constructors. No runtime behaviour changes — PyCharm users will get accurate IDE feedback after updating.
---

This release fixes a PyCharm false positive where classes decorated with `@strawberry.type` and `@strawberry.input` reported "Unexpected argument" on their generated keyword constructors.
