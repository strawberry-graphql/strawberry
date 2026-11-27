---
release type: patch
---

This release fixes `strawberry codegen` crashing with a `RecursionError` when an
operation variable uses an input type that refers to itself, directly or through
other input types, like `input IssueFilter { and: [IssueFilter!] }`.

The input type is now generated once. In the Python output, references to a class
that is defined further down (or to the class itself) are quoted, so the generated
module can be imported:

```python
class IssueFilter:
    title: Optional[str] = None
    any_of: Optional[list["IssueFilter"]] = None
```
