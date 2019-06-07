import inspect
import typing

import dataclasses
from graphql import GraphQLField, GraphQLInputField

from .constants import IS_STRAWBERRY_FIELD, IS_STRAWBERRY_INPUT
from .exceptions import MissingArgumentsAnnotationsError, MissingReturnAnnotationError
from .type_converter import REGISTRY, get_graphql_type_for_annotation
from .utils.dict_to_type import dict_to_type
from .utils.inspect import get_func_args
from .utils.lazy_property import lazy_property
from .utils.str_converters import to_camel_case, to_snake_case
from .utils.typing import (
    get_list_annotation,
    get_optional_annotation,
    is_list,
    is_optional,
)


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
    ):
        self._wrapped_obj = obj
        self.is_subscription = is_subscription
        self.is_input = is_input
        self.field_name = name
        self.field_resolver = resolver
        self.field_description = description

        if callable(self._wrapped_obj):
            self._check_has_annotations(self._wrapped_obj)

    def _check_has_annotations(self, func):
        # using annotations without passing from typing.get_type_hints
        # as we don't the actually types for the annotations
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

    @lazy_property
    def field(self):
        return _get_field(
            self._wrapped_obj,
            is_input=self.is_input,
            is_subscription=self.is_subscription,
            name=self.field_name,
            description=self.field_description,
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
    ):
        self.field_name = name
        self.field_description = description
        self.field_resolver = resolver
        self.is_subscription = is_subscription
        self.is_input = is_input

        super().__init__(
            # TODO:
            default=dataclasses.MISSING,
            default_factory=dataclasses.MISSING,
            init=False,
            repr=True,
            hash=None,
            # TODO: this needs to be False when init is False
            # we could turn it to True when and if we have a default
            # probably can't be True when passing a resolver
            compare=False,
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
        )


def convert_args(args, annotations):
    """Converts a nested dictionary to a dictionary of strawberry input types."""

    converted_args = {}

    for key, value in args.items():
        key = to_snake_case(key)
        annotation = annotations[key]

        # we don't need to check about unions here since they are not
        # yet supported for arguments.
        # see https://github.com/graphql/graphql-spec/issues/488

        is_list_of_args = False

        if is_optional(annotation):
            annotation = get_optional_annotation(annotation)

        if is_list(annotation):
            annotation = get_list_annotation(annotation)
            is_list_of_args = True

        if getattr(annotation, IS_STRAWBERRY_INPUT, False):
            if is_list_of_args:
                converted_args[key] = [dict_to_type(x, annotation) for x in value]
            else:
                converted_args[key] = dict_to_type(value, annotation)
        else:
            converted_args[key] = value

    return converted_args


def _get_field(
    wrap, *, is_input=False, is_subscription=False, name=None, description=None
):
    name = wrap.__name__

    annotations = typing.get_type_hints(wrap, None, REGISTRY)
    parameters = inspect.signature(wrap).parameters
    field_type = get_graphql_type_for_annotation(annotations["return"], name)

    arguments_annotations = {
        key: value
        for key, value in annotations.items()
        if key not in ["info", "return"]
    }

    arguments = {
        to_camel_case(name): get_graphql_type_for_annotation(
            annotation, name, parameters[name].default != inspect._empty
        )
        for name, annotation in arguments_annotations.items()
    }

    def resolver(source, info, **args):
        args = convert_args(args, arguments_annotations)

        return wrap(source, info, **args)

    field_params = {}

    if not is_input:
        field_params["args"] = arguments

        if is_subscription:

            def _resolve(event, info):
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
    )

    # when calling this with parens we are going to return a strawberry_field
    # instance, so it can be used as both decorator and function.

    if wrap is None:
        return field

    # otherwise we run the decorator directly,
    # when called as @strawberry.field, without parens.

    return field(wrap)
