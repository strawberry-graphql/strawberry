Release type: patch

For federation schema types has been added a posibility to implement `resolve_references` method.
Such implementation can have `info` parameter and also a parameter which hols a list of unique identificators.
Usually those identificators are ids primary keys. This parameter must have same name as it has in
implementation of method `resolve_reference`.

Such possibility allows to query for entities in database with one query. This can speed up response
for large federation queries.

`resolve_references` method is not mandatory, if it is not implemented, `resolve_reference` method is used.
