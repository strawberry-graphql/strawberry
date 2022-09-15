import importlib
import inspect
import warnings
from dataclasses import dataclass
from typing import ForwardRef, Generic, Optional, Type, TypeVar, cast


TypeName = TypeVar("TypeName")
Module = TypeVar("Module")


@dataclass(frozen=True)
class LazyType(Generic[TypeName, Module]):
    type_name: str
    module: str
    package: Optional[str] = None

    def __class_getitem__(cls, params):
        warnings.warn(
            (
                "LazyType is deprecated, use "
                "Annotated[YourType, strawberry.lazy(path)] instead"
            ),
            DeprecationWarning,
            stacklevel=2,
        )

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


class StrawberryLazyReference:
    def __init__(self, module: str) -> None:
        self.module = module
        self.package = None

        if module.startswith("."):
            frame = inspect.stack()[2][0]
            # TODO: raise a nice error if frame is None
            assert frame is not None
            assert frame.f_back is not None
            self.package = cast(str, frame.f_back.f_globals["__package__"])

    def resolve_forward_ref(self, forward_ref: ForwardRef) -> LazyType:
        return LazyType(forward_ref.__forward_arg__, self.module, self.package)


def lazy(module_path: str) -> StrawberryLazyReference:
    return StrawberryLazyReference(module_path)
