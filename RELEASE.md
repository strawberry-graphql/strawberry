Release type: patch

Calling `.clean(key)` on default dataloader with non-existing `key` will not throw `KeyError` anymore. Example:
```python
from strawberry.dataloader import DataLoader

async def load_data(keys):
    return [str(key) for key in keys]


dataloader = DataLoader(load_fn=load_data)
dataloader.clean(42)  # does not throw KeyError anymore
```

This is a patch release with no breaking changes.
