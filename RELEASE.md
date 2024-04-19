Release type: minor

This release improves the schema codegen, making it more robust and easier to
use.

It does this by introducing a directed acyclic graph for the schema codegen,
which should reduce the amount of edits needed to make the generated code work,
since it will be able to generate the code in the correct order (based on the
dependencies of each type).
