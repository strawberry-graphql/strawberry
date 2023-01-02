Release type: minor

This PR introduces context-manager driven global hooks.
i.e:
```python
def on_request(self) -> Iterable[None]:
    #  This part is called when a GraphQL request starts
    yield
    # This part is called when a GraphQL request ends
```

Issues fixed by this PR:
[#1864](https://github.com/strawberry-graphql/strawberry/issues/1864)
