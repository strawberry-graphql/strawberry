import dataclasses
import enum
import inspect
import typing

from graphql import GraphQLArgument, GraphQLField, GraphQLInputField, Undefined

from .constants import IS_STRAWBERRY_FIELD
from .exceptions import MissingArgumentsAnnotationsError, MissingReturnAnnotationError
from .type_converter import get_graphql_type_for_annotation
from .type_registry import get_registered_types
from .utils.arguments import convert_args
from .utils.inspect import get_func_args
from .utils.lazy_property import lazy_property
from .utils.str_converters import to_camel_case


class LazyFieldWrapper:
    """A lazy wrapper for a strawberry field.
    This allows to use cyclic dependencies in a strawberry fields:

    >>> @strawberry.type
    >>> class TypeA:
    >>>     @strawberry.field
    >>>     def type_b(self, info) -> "TypeB":
    >>>         from .type_b import TypeB
    >>>         return TypeB()
    """

    def __init__(
        self,
        obj,
        *,
        is_input=False,
        is_subscription=False,
        resolver=None,
        name=None,
        description=None,
        permission_classes=None
    ):
        self._wrapped_obj = obj
        self.is_subscription = is_subscription
        self.is_input = is_input
        self.field_name = name
        self.field_resolver = resolver
        self.field_description = description
        self.permission_classes = permission_classes or []

        if callable(self._wrapped_obj):
            self._check_has_annotations(self._wrapped_obj)

    def _check_has_annotations(self, func):
        # using annotations without passing from typing.get_type_hints
        # as we don't need the actually types for the annotations
        annotations = func.__annotations__
        name = func.__name__

        if "return" not in annotations:
            raise MissingReturnAnnotationError(name)

        function_arguments = set(get_func_args(func)) - {"root", "self", "info"}

        arguments_annotations = {
            key: value
            for key, value in annotations.items()
            if key not in ["root", "info", "return"]
        }

        annotated_function_arguments = set(arguments_annotations.keys())
        arguments_missing_annotations = (
            function_arguments - annotated_function_arguments
        )

        if len(arguments_missing_annotations) > 0:
            raise MissingArgumentsAnnotationsError(name, arguments_missing_annotations)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)

        return getattr(self._wrapped_obj, attr)

    def __call__(self, *args, **kwargs):
        return self._wrapped_obj(self, *args, **kwargs)

    def _get_permissions(self):
        """
        Gets all permissions defined in the permission classes
        >>> strawberry.field(permission_classes=[IsAuthenticated])
        """
        return (permission() for permission in self.permission_classes)

    def _check_permissions(self, source, info, **kwargs):
        """
        Checks if the permission should be accepted and
        raises an exception if not
        """
        for permission in self._get_permissions():
            if not permission.has_permission(source, info, **kwargs):
                message = getattr(permission, "message", None)
                raise PermissionError(message)

    @lazy_property
    def graphql_type(self):
        return _get_field(
            self._wrapped_obj,
            is_input=self.is_input,
            is_subscription=self.is_subscription,
            name=self.field_name,
            description=self.field_description,
            check_permission=self._check_permissions,
        )


class strawberry_field(dataclasses.Field):
    """A small wrapper for a field in strawberry.

    You shouldn't be using this directly as this is used internally
    when using `strawberry.field`.

    This allows to use the following two syntaxes when using the type
    decorator:

    >>> class X:
    >>>     field_abc: str = strawberry.field(description="ABC")

    >>> class X:
    >>>     @strawberry.field(description="ABC")
    >>>     def field_a(self, info) -> str:
    >>>         return "abc"

    When calling this class as strawberry_field it creates a field
    that stores metadata (such as field description). In addition
    to that it also acts as decorator when called as a function,
    allowing us to us both syntaxes.
    """

    def __init__(
        self,
        *,
        is_input=False,
        is_subscription=False,
        resolver=None,
        name=None,
        description=None,
        metadata=None,
        permission_classes=None
    ):
        self.field_name = name
        self.field_description = description
        self.field_resolver = resolver
        self.is_subscription = is_subscription
        self.is_input = is_input
        self.field_permission_classes = permission_classes

        super().__init__(
            # TODO:
            default=dataclasses.MISSING,
            default_factory=dataclasses.MISSING,
            init=resolver is None,
            repr=True,
            hash=None,
            # TODO: this needs to be False when init is False
            # we could turn it to True when and if we have a default
            # probably can't be True when passing a resolver
            compare=is_input,
            metadata=metadata,
        )

    def __call__(self, wrap):
        setattr(wrap, IS_STRAWBERRY_FIELD, True)

        self.field_description = self.field_description or wrap.__doc__

        return LazyFieldWrapper(
            wrap,
            is_input=self.is_input,
            is_subscription=self.is_subscription,
            resolver=self.field_resolver,
            name=self.field_name,
            description=self.field_description,
            permission_classes=self.field_permission_classes,
        )


def _get_field(
    wrap,
    *,
    is_input=False,
    is_subscription=False,
    name=None,
    description=None,
    check_permission=None
):
    name = wrap.__name__

    annotations = typing.get_type_hints(wrap, None, get_registered_types())
    parameters = inspect.signature(wrap).parameters
    field_type = get_graphql_type_for_annotation(annotations["return"], name)

    arguments_annotations = {
        key: value
        for key, value in annotations.items()
        if key not in ["info", "return"]
    }

    arguments = {}
    for name, annotation in arguments_annotations.items():
        default = parameters[name].default
        arguments[to_camel_case(name)] = GraphQLArgument(
            get_graphql_type_for_annotation(annotation, name, default is None),
            default_value=Undefined if default in (inspect._empty, None) else default,
        )

    def resolver(source, info, **kwargs):
        if check_permission:
            check_permission(source, info, **kwargs)

        # the following code allows to omit info and root arguments
        # by inspecting the original resolver arguments,
        # if it asks for self, the source will be passed as first argument
        # if it asks for root, the source it will be passed as kwarg
        # if it asks for info, the info will be passed as kwarg

        kwargs = convert_args(kwargs, arguments_annotations)
        function_args = get_func_args(wrap)

        args = []

        if "self" in function_args:
            args.append(source)

        if "root" in function_args:
            kwargs["root"] = source

        if "info" in function_args:
            kwargs["info"] = info

        result = wrap(*args, **kwargs)

        # graphql-core expects a resolver for an Enum type to return
        # the enum's *value* (not its name or an instance of the enum).
        if isinstance(result, enum.Enum):
            return result.value

        return result

    field_params = {}

    if not is_input:
        field_params["args"] = arguments

        if is_subscription:

            def _resolve(event, info, **kwargs):
                if check_permission:
                    check_permission(event, info, **kwargs)

                return event

            field_params.update({"subscribe": resolver, "resolve": _resolve})
        else:
            field_params.update({"resolve": resolver})

    field_params["description"] = description or wrap.__doc__

    FieldType = GraphQLInputField if is_input else GraphQLField

    return FieldType(field_type, **field_params)


def field(
    wrap=None,
    *,
    name=None,
    description=None,
    resolver=None,
    is_input=False,
    is_subscription=False,
    permission_classes=None
):
    """Annotates a method or property as a GraphQL field.

    This is normally used inside a type declaration:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = strawberry.field(description="ABC")

    >>>     @strawberry.field(description="ABC")
    >>>     def field_with_resolver(self, info) -> str:
    >>>         return "abc"

    it can be used both as decorator and as a normal function.
    """

    field = strawberry_field(
        name=name,
        description=description,
        resolver=resolver,
        is_input=is_input,
        is_subscription=is_subscription,
        permission_classes=permission_classes,
    )

    # when calling this with parens we are going to return a strawberry_field
    # instance, so it can be used as both decorator and function.

    if wrap is None:
        return field

    # otherwise we run the decorator directly,
    # when called as @strawberry.field, without parens.

    return field(wrap)
