Release type: patch

Added automatic GraphQL type generation for Django models.

Usage:

```python
# models.py
from django.db import models

class Todo(models.Model):
    name = models.CharField(max_length=250)
    done = models.BooleanField(default=False)

# types.py
from todo.models import Todo
from strawberry.contrib.django.type import model_type

@model_type(model=Todo, fields=['id', 'name', 'done'])
class TodoType:
    pass

# Generated type:
type TodoType {
    id: ID!
    name: String!
    done: Boolean!
}
```