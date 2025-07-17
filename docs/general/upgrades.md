---
title: Upgrading Strawberry
---

# Upgrading Strawberry

<!--alex ignore-->

We try to keep Strawberry as backwards compatible as possible, but sometimes we
need to make updates to the public API. While we try to deprecate APIs before
removing them, we also want to make it as easy as possible to upgrade to the
latest version of Strawberry.

For this reason, we provide a CLI command to run Codemods that can automatically
upgrade your codebase to use the updated APIs.

Keep an eye on our release notes and the
[breaking changes](../breaking-changes.md) page to see if a new Codemod is
available, or if manual changes are required.

Here's an example of how to upgrade your codebase by running a Codemod using the
Strawberry CLI's `upgrade` command:

```shell
strawberry upgrade annotated-union .
```
