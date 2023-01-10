Release type: minor

This release changes the way scoped extensions hooks work.
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

Note that the old style hooks entered to a deprecation progress.
