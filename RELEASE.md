Release type: minor

This release implements the ability to use custom caching for dataloaders.
It also allows to provide a `cache_key_fn` to the dataloader. This function
is used to generate the cache key for the dataloader. This is useful when
you want to use a custom hashing function for the cache key.
