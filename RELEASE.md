Release type: patch

The return type annotation for `DataLoader.load` and `load_many` no longer
includes any exceptions directly returned by the `load_fn`. The ability to
handle errors by returning them as elements from `load_fn` is now documented too.
