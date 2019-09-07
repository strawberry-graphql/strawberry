from typing import Optional

import pytest

from django.db import models

import strawberry
from strawberry.contrib.django.converter import convert_django_field


str_fields = [
    models.fields.CharField,
    models.fields.TextField,
    models.fields.EmailField,
    models.fields.SlugField,
    models.fields.URLField,
    models.fields.GenericIPAddressField,
    models.fields.FilePathField,
    models.fields.UUIDField,
    models.fields.files.FileField,
    models.fields.files.ImageField,
]

int_fields = [
    models.fields.PositiveIntegerField,
    models.fields.PositiveSmallIntegerField,
    models.fields.SmallIntegerField,
    models.fields.BigIntegerField,
    models.fields.IntegerField,
]

float_fields = [
    models.fields.DecimalField,
    models.fields.FloatField,
    models.fields.DurationField,
]


@pytest.mark.parametrize("FieldType", str_fields)
def test_converter_returns_str(FieldType):
    assert convert_django_field(FieldType()) == str
    assert convert_django_field(FieldType(null=True)) == Optional[str]


@pytest.mark.parametrize("FieldType", int_fields)
def test_converter_returns_int(FieldType):
    assert convert_django_field(FieldType()) == int
    assert convert_django_field(FieldType(null=True)) == Optional[int]


@pytest.mark.parametrize("FieldType", float_fields)
def test_converter_returns_float(FieldType):
    assert convert_django_field(FieldType()) == float
    assert convert_django_field(FieldType(null=True)) == Optional[float]


def test_converter_returns_bool():
    assert convert_django_field(models.fields.BooleanField()) == bool
    assert convert_django_field(models.fields.NullBooleanField()) == Optional[bool]


def test_converter_returns_id():
    assert convert_django_field(models.fields.AutoField()) == strawberry.ID
    assert (
        convert_django_field(models.fields.AutoField(null=True))
        == Optional[strawberry.ID]
    )
