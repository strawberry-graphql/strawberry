from typing import Optional

from django.db import models

import strawberry
from strawberry.contrib.django.converter import convert_django_field


def test_converter_returns_correct_type():

    for FieldType in [
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
    ]:
        assert convert_django_field(FieldType()) == str
        assert convert_django_field(FieldType(null=True)) == Optional[str]

    for FieldType in [
        models.fields.PositiveIntegerField,
        models.fields.PositiveSmallIntegerField,
        models.fields.SmallIntegerField,
        models.fields.BigIntegerField,
        models.fields.IntegerField,
    ]:
        assert convert_django_field(FieldType()) == int
        assert convert_django_field(FieldType(null=True)) == Optional[int]

    for FieldType in [
        models.fields.DecimalField,
        models.fields.FloatField,
        models.fields.DurationField,
    ]:
        assert convert_django_field(FieldType()) == float
        assert convert_django_field(FieldType(null=True)) == Optional[float]

    assert convert_django_field(models.fields.AutoField()) == strawberry.ID
    assert (
        convert_django_field(models.fields.AutoField(null=True))
        == Optional[strawberry.ID]
    )

    assert convert_django_field(models.fields.BooleanField()) == bool
    assert convert_django_field(models.fields.NullBooleanField()) == Optional[bool]
