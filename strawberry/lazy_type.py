import importlib
import inspect
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ForwardRef,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)

if TYPE_CHECKING:
    from typing_extensions import Self

TypeName = TypeVar("TypeName")
Module = TypeVar("Module")


@dataclass(frozen=True)
class LazyType(Generic[TypeName, Module]):
    type_name: str
    module: str
    package: Optional[str] = None

    def __class_getitem__(cls, params: Tuple[str, str]) -> "Self":
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

    def resolve_type(self) -> Type[Any]:
        module = importlib.import_module(self.module, self.package)
        main_module = sys.modules.get("__main__", None)
        if main_module:
            # If lazy type points to the main module, use it instead of the imported
            # module. Otherwise duplication checks during schema-conversion might fail.
            # Refer to: https://github.com/strawberry-graphql/strawberry/issues/2397
            if main_module.__spec__ and main_module.__spec__.name == self.module:
                module = main_module
            elif hasattr(main_module, "__file__") and hasattr(module, "__file__"):
                main_file = main_module.__file__
                module_file = module.__file__
                if main_file and module_file:
                    try:
                        is_samefile = Path(main_file).samefile(module_file)
                    except FileNotFoundError:
                        # Can be raised when run through the CLI as the __main__ file
                        # path contains `strawberry.exe`
                        is_samefile = False
                    module = main_module if is_samefile else module
        return module.__dict__[self.type_name]

    # this empty call method allows LazyTypes to be used in generic types
    # for example: List[LazyType["A", "module"]]

    def __call__(self) -> None:  # pragma: no cover
        return None


class StrawberryLazyReference:
    def __init__(self, module: str) -> None:
        self.module = module
        self.package = None

        if module.startswith("."):
            frame = sys._getframe(2)
            # TODO: raise a nice error if frame is None
            assert frame is not None
            self.package = cast(str, frame.f_globals["__package__"])

    def resolve_forward_ref(self, forward_ref: ForwardRef) -> LazyType:
        return LazyType(forward_ref.__forward_arg__, self.module, self.package)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StrawberryLazyReference):
            return NotImplemented

        return self.module == other.module and self.package == other.package

    def __hash__(self) -> int:
        return hash((self.__class__, self.module, self.package))


def lazy(module_path: str) -> StrawberryLazyReference:
    return StrawberryLazyReference(module_path)
