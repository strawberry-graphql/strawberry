from typing import TYPE_CHECKING, Optional, Type

from strawberry.annotation import StrawberryAnnotation
from strawberry.auto import StrawberryAuto
from strawberry.experimental.pydantic.object_type import get_type_for_field
from strawberry.experimental.pydantic.utils import ensure_all_auto_fields_in_pydantic
from strawberry.extensions.type_extensions import TypeExtension

if TYPE_CHECKING:
    from pydantic.fields import ModelField

    from strawberry.experimental.pydantic.conversion_types import PydanticModel
    from strawberry.field import StrawberryField
    from strawberry.types.types import TypeDefinition


class PydanticTypeExtension(TypeExtension):
    def __init__(
        self,
        model: Type[PydanticModel],
        *,
        name: Optional[str] = None,
        is_input: bool = False,
        is_interface: bool = False,
        all_fields: bool = False,
        use_pydantic_alias: bool = True,
    ):
        self.model = model
        self.use_pydantic_alias = use_pydantic_alias

    def apply(self, strawberry_type: TypeDefinition) -> None:
        auto_fields: list[StrawberryField] = []

        for field in strawberry_type.fields:
            if isinstance(field.type, StrawberryAuto):
                # Handle this auto field
                auto_fields.append(field)

        ensure_all_auto_fields_in_pydantic(
            model=self.model,
            auto_fields={field.python_name for field in auto_fields},
            cls_name=strawberry_type.name,
        )

        for field in auto_fields:
            model_field: ModelField = self.model.__fields__[field.python_name]
            field_type = get_type_for_field(model_field, strawberry_type.is_input)
            field.type_annotation = StrawberryAnnotation.from_annotation(field_type)

            if self.use_pydantic_alias and model_field.has_alias:
                field.graphql_name = model_field.alias
        pass

        if strawberry_type.is_input:
            self.model._strawberry_input_type = strawberry_type.origin  # type: ignore
        else:
            self.model._strawberry_type = strawberry_type.origin  # type: ignore
        strawberry_type._pydantic_type = self.model
