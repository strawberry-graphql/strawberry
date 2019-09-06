from django.db import models


class TestModel(models.Model):
    name = models.CharField(max_length=50)
