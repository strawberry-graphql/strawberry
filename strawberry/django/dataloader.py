from typing import Type

from asgiref.sync import sync_to_async

from django.db import models


def create_model_load_fn(django_model: Type[models.Model]):
    if not issubclass(django_model, models.Model):
        raise Exception(
            (
                "Object passed to `created_model_load_fn` has to be a Django model. "
                f"Recieved: {django_model}"
            )
        )

    @sync_to_async
    def load_model(keys):
        qs = django_model.objects.filter(pk__in=keys)
        instance_map = {inst.id: inst for inst in qs}

        return [instance_map.get(key) for key in keys]

    return load_model
