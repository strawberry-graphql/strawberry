from typing import Union

from strawberry.types import StrawberryField

_FIELD_FED_TYPE = Union[StrawberryField, 'StrawberryFederatedField']


class StrawberryFederatedField(StrawberryField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.external = ...
        self.provides = ...
        self.requires = ...


def external(field: _FIELD_FED_TYPE) -> StrawberryFederatedField:
    if isinstance(field, StrawberryField):
        ...
    if isinstance(field, StrawberryFederatedField):
        field.external = ...


def provides(field: _FIELD_FED_TYPE) -> StrawberryFederatedField:
    if isinstance(field, StrawberryField):
        ...
    if isinstance(field, StrawberryFederatedField):
        field.provides = ...


def requires(field: _FIELD_FED_TYPE) -> StrawberryFederatedField:
    if isinstance(field, StrawberryField):
        ...
    if isinstance(field, StrawberryFederatedField):
        field.requires = ...
