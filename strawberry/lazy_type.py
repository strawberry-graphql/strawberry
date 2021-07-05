import importlib
import inspect
from dataclasses import dataclass
from typing import Generic, Optional, Type, TypeVar


TypeName = TypeVar("TypeName")
Module = TypeVar("Module")


@dataclass(frozen=True)
class LazyType(Generic[TypeName, Module]):
    type_name: str
    module: str
    package: Optional[str]

    def __class_getitem__(cls, params):
        type_name, module = params

        package = None

        if module.startswith("."):
            current_frame = inspect.currentframe()
            package = current_frame.f_back.f_globals["__package__"]  # type: ignore

        return cls(type_name, module, package)

    def resolve_type(self) -> Type:
        module = importlib.import_module(self.module, self.package)

        return module.__dict__[self.type_name]

    # this empty call method allows LazyTypes to be used in generic types
    # for example: List[LazyType["A", "module"]]

    def __call__(self):  # pragma: no cover
        return None
