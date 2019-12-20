from django.db import models


class Example(models.Model):
    name = models.CharField(max_length=100)
