---
release type: patch
---

This release fixes type variable resolution for specialized generic subclasses
when fields return nested generics (such as `Box[T]`) or define arguments
typed with generic parameters (such as `take(self, value: T)`).

Previously, specialized generic subclasses only substituted type parameters for
return annotations that were direct `StrawberryType` instances, leaving generic
type aliases with unbound type variables. Field arguments also were not passed the
subclass type definition or origin during schema conversion and runtime argument
coercion. Both cases now resolve type variables against the specialized subclass.
