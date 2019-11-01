from functools import singledispatch
from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from django.db import models

import strawberry


@singledispatch
def convert_django_field(field):
    raise ImproperlyConfigured(
        f"Don't know how to convert the Django model "
        + "field {field} ({field.__class__}) to type"
    )


def type_or_optional_wrapped(type_, required):
    if required:
        return type_

    return Optional[type_]


@convert_django_field.register(models.fields.CharField)
@convert_django_field.register(models.fields.TextField)
@convert_django_field.register(models.fields.EmailField)
@convert_django_field.register(models.fields.SlugField)
@convert_django_field.register(models.fields.URLField)
@convert_django_field.register(models.fields.GenericIPAddressField)
@convert_django_field.register(models.fields.FilePathField)
@convert_django_field.register(models.fields.UUIDField)
@convert_django_field.register(models.fields.files.FileField)
@convert_django_field.register(models.fields.files.ImageField)
def convert_django_field_to_string(field):
    return type_or_optional_wrapped(str, not field.null)


@convert_django_field.register(models.fields.AutoField)
def convert_django_field_to_id(field):
    return type_or_optional_wrapped(strawberry.ID, not field.null)


@convert_django_field.register(models.fields.PositiveIntegerField)
@convert_django_field.register(models.fields.PositiveSmallIntegerField)
@convert_django_field.register(models.fields.SmallIntegerField)
@convert_django_field.register(models.fields.BigIntegerField)
@convert_django_field.register(models.fields.IntegerField)
def convert_django_field_to_int(field):
    return type_or_optional_wrapped(int, not field.null)


@convert_django_field.register(models.fields.BooleanField)
def convert_django_field_to_boolean(field):
    return type_or_optional_wrapped(bool, True)


@convert_django_field.register(models.fields.NullBooleanField)
def convert_django_field_to_nullboolean(field):
    return type_or_optional_wrapped(bool, False)


@convert_django_field.register(models.fields.DecimalField)
@convert_django_field.register(models.fields.FloatField)
@convert_django_field.register(models.fields.DurationField)
def convert_django_field_to_float(field):
    return type_or_optional_wrapped(float, not field.null)
