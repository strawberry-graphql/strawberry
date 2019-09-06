from functools import singledispatch
from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from django.db import models

import strawberry


@singledispatch
def convert_django_field_to_resolver(field):
    raise ImproperlyConfigured(
        "Don't know how to convert the Django form field %s (%s) "
        "to type" % (field, field.__class__)
    )


def type_or_optional_wrapped(type_, required):
    if required:
        return type_

    return Optional[type_]


@convert_django_field_to_resolver.register(models.fields.CharField)
@convert_django_field_to_resolver.register(models.fields.TextField)
@convert_django_field_to_resolver.register(models.fields.EmailField)
@convert_django_field_to_resolver.register(models.fields.SlugField)
@convert_django_field_to_resolver.register(models.fields.URLField)
@convert_django_field_to_resolver.register(models.fields.GenericIPAddressField)
@convert_django_field_to_resolver.register(models.fields.FilePathField)
@convert_django_field_to_resolver.register(models.fields.UUIDField)
def convert_django_field_to_string_resolver(field):
    type_ = type_or_optional_wrapped(str, not field.null)

    @strawberry.field
    def resolver(self, info) -> type_:
        return getattr(self, field.name)

    return resolver


@convert_django_field_to_resolver.register(models.fields.AutoField)
def convert_django_field_to_id_resolver(field):
    type_ = type_or_optional_wrapped(strawberry.ID, not field.null)

    @strawberry.field
    def resolver(self, info) -> type_:
        return getattr(self, field.name)

    return resolver


@convert_django_field_to_resolver.register(models.fields.PositiveIntegerField)
@convert_django_field_to_resolver.register(models.fields.PositiveSmallIntegerField)
@convert_django_field_to_resolver.register(models.fields.SmallIntegerField)
@convert_django_field_to_resolver.register(models.fields.BigIntegerField)
@convert_django_field_to_resolver.register(models.fields.IntegerField)
def convert_django_field_to_int_resolver(field):
    type_ = type_or_optional_wrapped(int, not field.null)

    @strawberry.field
    def resolver(self, info) -> type_:
        return getattr(self, field.name)

    return resolver


@convert_django_field_to_resolver.register(models.fields.BooleanField)
def convert_django_field_to_boolean_resolver(field):
    type_ = type_or_optional_wrapped(bool, True)

    @strawberry.field
    def resolver(self, info) -> type_:
        return getattr(self, field.name)

    return resolver


@convert_django_field_to_resolver.register(models.fields.NullBooleanField)
def convert_django_field_to_nullboolean_resolver(field):
    type_ = type_or_optional_wrapped(bool, False)

    @strawberry.field
    def resolver(self, info) -> type_:
        return getattr(self, field.name)

    return resolver


@convert_django_field_to_resolver.register(models.fields.DecimalField)
@convert_django_field_to_resolver.register(models.fields.FloatField)
@convert_django_field_to_resolver.register(models.fields.DurationField)
def convert_django_field_to_float_resolver(field):
    type_ = type_or_optional_wrapped(float, not field.null)

    @strawberry.field
    def resolver(self, info) -> type_:
        return getattr(self, field.name)

    return resolver


@convert_django_field_to_resolver.register(models.fields.files.FileField)
@convert_django_field_to_resolver.register(models.fields.files.ImageField)
def convert_django_field_to_url_resolver(field):
    type_ = type_or_optional_wrapped(float, not field.null)

    @strawberry.field
    def resolver(self, info) -> type_:
        return getattr(self, field.name + ".url")

    return resolver
