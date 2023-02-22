Release type: minor

This release changes how extension hooks are defined. The new style hooks are
more flexible and allow to run code before and after the execution.

The old style hooks are still supported but will be removed in future releases.

**Before:**

```python
def on_execution_started(self):  # Called before the execution start
    ...


def on_execution_end(self):  # Called after the execution ends
    ...
```

**After**

```python
def on_execute(self):
    #  This part is called before the execution start
    yield
    #  This part is called after the execution ends
```
