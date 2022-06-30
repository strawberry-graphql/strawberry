from __future__ import annotations

from dataclasses import InitVar, dataclass, field

from strawberry.description_source import DescriptionSources
from strawberry.schema.name_converter import NameConverter


@dataclass
class StrawberryConfig:
    auto_camel_case: InitVar[bool] = None
    name_converter: NameConverter = field(default_factory=NameConverter)
    description_sources: DescriptionSources = DescriptionSources.STRAWBERRY_DESCRIPTIONS

    def __post_init__(
        self,
        auto_camel_case: bool,
    ):
        if auto_camel_case is not None:
            self.name_converter.auto_camel_case = auto_camel_case
