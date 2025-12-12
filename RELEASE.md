Release type: patch

Fix compatibility with Python 3.14 when using the Pydantic integration with Pydantic V2.

Previously, importing `strawberry.experimental.pydantic` on Python 3.14 would trigger:
```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```

This is now fixed by avoiding `pydantic.v1` imports on Python 3.14+.
