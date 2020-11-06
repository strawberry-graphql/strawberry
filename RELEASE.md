Release type: minor

This release adds a built-in dataloader. Example:

```python
async def app():
    async def idx(keys):
        return keys

    loader = DataLoader(load_fn=idx)

    [value_a, value_b, value_c] = await asyncio.gather(
        loader.load(1),
        loader.load(2),
        loader.load(3),
    )


    assert value_a == 1
    assert value_b == 2
    assert value_c == 3
```
