Release type: patch

This release fixes an issue where annotations on `@strawberry.type`s were overridden
by our code. With release all annotations should be preserved.

This is useful for libraries that use annotations to introspect Strawberry types.
