Release type: minor

This release improves the dataloader class with new features:

- Explicitly cache invalidation, prevents old data from being fetched after a mutation
- Importing data into the cache, prevents unnecessary load calls if the data has already been fetched by other means.
