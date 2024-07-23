import importlib
import inspect
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    ForwardRef,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import Self

TypeName = TypeVar("TypeName")
Module = TypeVar("Module")
Other = TypeVar("Other")


@dataclass(frozen=True)
class LazyType(Generic[TypeName, Module]):
    """A class that represents a type that will be resolved at runtime.

    This is useful when you have circular dependencies between types.

    This class is not meant to be used directly, instead use the `strawberry.lazy`
    function.
    """

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

    def __or__(self, other: Other) -> object:
        return Union[self, other]

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
    """A class that represents a lazy reference to a type in another module.

    This is useful when you have circular dependencies between types.

    This class is not meant to be used directly, instead use the `strawberry.lazy`
    function.
    """

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
    """Creates a lazy reference to a type in another module.

    Args:
        module_path: The path to the module containing the type, supports relative paths
            starting with `.`

    Returns:
        A `StrawberryLazyReference` object that can be used to reference a type in another
        module.

    This is useful when you have circular dependencies between types.

    For example, assuming you have a `Post` type that has a field `author` that
    references a `User` type (which also has a field `posts` that references a list of
    `Post`), you can use `strawberry.lazy` to avoid the circular dependency:

    ```python
    from typing import TYPE_CHECKING, Annotated

    import strawberry

    if TYPE_CHECKING:
        from .users import User


    @strawberry.type
    class Post:
        title: str
        author: Annotated["User", strawberry.lazy(".users")]
    ```
    """
    return StrawberryLazyReference(module_path)


__all__ = ["LazyType", "StrawberryLazyReference", "lazy"]
