Release type: minor

Add `strawberry.federation.params` module with shared TypedDicts (`FederationFieldParams`, `FederationInterfaceParams`, `FederationTypeParams`) and processing functions (`process_federation_field_directives`, `process_federation_type_directives`) for federation directives.

These TypedDicts can be consumed via `Unpack[...]` to avoid duplicating federation parameter lists across packages. The processing functions are extracted from inline logic previously in `field.py` and `object_type.py`.

Also fixes a bug where `inaccessible=False` incorrectly added the `Inaccessible` directive on types/interfaces.
