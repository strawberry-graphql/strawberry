import importlib
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Optional, Type, TypeVar

from typing_extensions import Annotated


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
            assert current_frame is not None
            assert current_frame.f_back is not None
            package = current_frame.f_back.f_globals["__package__"]

        return cls(type_name, module, package)

    def resolve_type(self) -> Type:
        module = importlib.import_module(self.module, self.package)

        return module.__dict__[self.type_name]

    # this empty call method allows LazyTypes to be used in generic types
    # for example: List[LazyType["A", "module"]]

    def __call__(self):  # pragma: no cover
        return None


if TYPE_CHECKING:  # pragma: no cover
    # Static types like pyright expects a type to be passed to generic classes, which
    # means that if we pass a string it will say the type is unknown, and if we import
    # the module they will say a module can't be used in place of a type.
    # This will tricky it into thinking that LazyType is Annotated, not only avoiding
    # the issue but also statically typing it correctly.
    Lazy = Annotated
else:
    Lazy = LazyType
