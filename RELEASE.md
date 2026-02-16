Release type: minor

Remove deprecated `channel_listen` method from the Channels integration, deprecated since [0.193.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.193.0).

### Migration guide

**Before (deprecated):**
```python
async for message in info.context["ws"].channel_listen("my_channel"):
    yield Message(message=message["text"])
```

**After:**
```python
async with info.context["ws"].listen_to_channel("my_channel") as listener:
    async for message in listener:
        yield Message(message=message["text"])
```
