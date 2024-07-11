Release type: patch

Calling `.clean(key)` on default dataloader with non-existing `key` will not throw `KeyError` error anymore. Example:
```python
async def load_data(keys):
    return [str(key) for key in keys]


dataloader = DataLoader(load_fn=load_data)
dataloader.clean(42)  # does not throw KeyError anymore
```

This is a patch release, so no breaking changes.
