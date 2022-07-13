from strawberry.custom_scalar import scalar


FieldSet = scalar(str, name="_FieldSet")

# TODO: this is not used yet
LinkImport = scalar(list, name="link__Import")
