Release type: minor

This release adds syntax sugar for permissions:

Until now, it requires a long-ish line of code:

```
field1: str = strawberry.field(permission_classes=[IsAuthenticated])
```

Now on it can also be specified using Annotated types:

```
field2: Annotated[str, IsAuthenticated]
value3: IsAuthenticated[str]
```
