from django.db import models


class DummyModel(models.Model):
    name = models.CharField(max_length=50)
    secret = models.CharField(max_length=50, null=True)
