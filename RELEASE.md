Release type: minor

This release introduces a new command called `upgrade`, this command can be used
to run codemods on your codebase to upgrade to the latest version of Strawberry.

At the moment we only support upgrading unions to use the new syntax with
annotated, but in future we plan to add more commands to help with upgrading.

Here's how you can use the command to upgrade your codebase:

```shell
strawberry upgrade annotated-union .
```
