Release type: minor

This PR introduces context-styled extensions global hooks.
i.e:
```python
def on_request(self) -> Iterable[None]:
    #  This part is called when a GraphQL request starts
    yield
    # This part is called when a GraphQL request ends

```
**Note: If you have any "old-style" hooks
they will be called instead of any "context-styled" hooks.**
