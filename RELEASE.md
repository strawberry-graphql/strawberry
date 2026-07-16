---
release type: patch
social_messages:
  x: >-
    {project_name} {version} keeps user-defined methods on experimental Pydantic types.
    🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} fixes experimental Pydantic types dropping user-defined
    static, class, and instance methods (and properties) from the decorated class body.
---

This release fixes `strawberry.experimental.pydantic.type` (and `.input` /
`.interface`) stripping user-defined methods from the decorated class.

Previously any `staticmethod`, `classmethod`, regular method, or `property` defined on
the class body — other than `from_pydantic` / `to_pydantic` — was dropped, because the
type is rebuilt with `make_dataclass` from the original bases rather than from the class
itself, so calling it raised `AttributeError`:

```python
@strawberry.experimental.pydantic.type(model=Foo)
class FooType:
    bar: strawberry.auto

    @staticmethod
    def do_something() -> str:
        return "done"


FooType.do_something()  # used to raise AttributeError
```

These members are now carried over and keep working at runtime.
