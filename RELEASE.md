Release type: minor

This release introduce a directed acyclic graph for the schema codegen, this
should reduce the amount of edits needed to make the generated code work, since
it will be able to generate the code in the correct order (based on the
dependencies of each type).
