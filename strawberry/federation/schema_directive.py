import dataclasses
from typing import Callable, List, Optional, Type, TypeVar
from typing_extensions import dataclass_transform

from strawberry.directive import directive_field
from strawberry.field import StrawberryField, field
from strawberry.object_type import _wrap_dataclass
from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.types.type_resolver import _get_fields


@dataclasses.dataclass
class ComposeOptions:
    import_url: Optional[str]


@dataclasses.dataclass
class StrawberryFederationSchemaDirective(StrawberrySchemaDirective):
    compose_options: Optional[ComposeOptions] = None


T = TypeVar("T", bound=Type)


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(directive_field, field, StrawberryField),
)
def schema_directive(
    *,
    locations: List[Location],
    description: Optional[str] = None,
    name: Optional[str] = None,
    repeatable: bool = False,
    print_definition: bool = True,
    compose: bool = False,
    import_url: Optional[str] = None,
) -> Callable[..., T]:
    def _wrap(cls: T) -> T:
        cls = _wrap_dataclass(cls)  # type: ignore
        fields = _get_fields(cls, {})

        cls.__strawberry_directive__ = StrawberryFederationSchemaDirective(
            python_name=cls.__name__,
            graphql_name=name,
            locations=locations,
            description=description,
            repeatable=repeatable,
            fields=fields,
            print_definition=print_definition,
            origin=cls,
            compose_options=ComposeOptions(import_url=import_url) if compose else None,
        )

        return cls

    return _wrap


__all__ = ["Location", "schema_directive"]
