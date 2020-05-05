Release type: minor

This release add supports for named unions, now you can create
a new union type by writing:

```python
Result = strawberry.union("Result", (A, B), description="Example Result")
```

This also improves the support for Union and Generic types, as it 
was broken before.

