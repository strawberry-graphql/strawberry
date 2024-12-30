from django.db import models


class Example(models.Model):  # noqa: DJ008
    name = models.CharField(max_length=100)
