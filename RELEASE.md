Release type: patch

This release fixes an issue where mypy would complain when using a typed async
resolver with `strawberry.field(resolver=...)`.

Now the code will type check correctly. We also updated our test suite to make
we catch similar issues in the future.
