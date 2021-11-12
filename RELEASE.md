Release type: minor

This release changes how we handle GraphQL names. It also introduces a new
configuration option called `name_converter`. This option allows you to specify
a custom `NameConverter` to be used when generating GraphQL names.

This is currently not documented because the API will change slightly in future
as we are working on renaming internal types.

This release also fixes an issue when creating concrete types from generic when
passing list objects.
