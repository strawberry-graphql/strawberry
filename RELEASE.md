---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Fixes Relay pagination returning the wrong items when `first` and `before` are combined. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This patch fixes a Relay connection pagination bug where combining `first` with `before` returned items from the wrong end of the list instead of the first N items before the cursor.
---

This release fixes a bug in Relay connection pagination where combining `first` with `before` returned the wrong slice of items — walking backward from the `before` cursor instead of taking the first `first` items among those before it, per the Relay Cursor Connections spec.
