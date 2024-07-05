Release type: minor

Support for schema-extensions in subscriptions.


This release also changes the signature of schema-extension lifespan hooks

Before:
```python
class QueryCacheExtension(SchemaExtension):

    async def on_operation(self):
        query = self.execution_context.query
        if cached := self.cache.get(query):
            self.execution_context.result = cached
        yield
        if not cached:
            self.cache.set(self.execution_context.query, self.execution_context.result)
```
This approuch can easly break because
The `execution_context` **can change during the execution** of the extension if there are multiple operations running
in parallel.

After:
```python
class QueryCacheExtension(SchemaExtension):

    async def on_operation(self, execution_context):
        if cached := self.cache.get(execution_context.query):
            execution_context.result = cached
        yield
        if not cached:
            self.cache.set(execution_context.query, execution_context.result)
```

Note that extensions that are following the previous signature will still work,
but it is recommended to update them.

___

This release also adds support for subscriptions in schema-extensions.
i.e:
```python
class MyExtension(SchemaExtension):

    async def on_operation(self, execution_context):
        #  This part is called before the subscription started
        yield
        #  This part is called after the subscription ended

    async def on_execute(self, execution_context):
        #  This part is called before a new result is comming from the subscription
        yield
        #  This part is called after the subscription yielded a result
```
