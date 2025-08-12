"""Test edge cases for input type support in JIT compiler."""

from enum import Enum
from typing import List, Optional

import strawberry
from strawberry.jit import compile_query


# Define an enum for input
@strawberry.enum
class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Complex nested input types
@strawberry.input
class MetadataInput:
    key: str
    value: str


@strawberry.input
class TagInput:
    name: str
    color: Optional[str] = None
    metadata: Optional[List[MetadataInput]] = None


@strawberry.input
class TaskInput:
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    tags: Optional[List[TagInput]] = None
    assignee_ids: Optional[List[str]] = None
    metadata: Optional[List[MetadataInput]] = None
    is_active: bool = True
    estimated_hours: Optional[float] = None


@strawberry.input
class BulkTaskInput:
    tasks: List[TaskInput]
    default_priority: Optional[Priority] = None
    auto_assign: bool = False


# Output types
@strawberry.type
class Metadata:
    key: str
    value: str


@strawberry.type
class Tag:
    id: str
    name: str
    color: Optional[str]
    metadata: List[Metadata]


@strawberry.type
class Task:
    id: str
    title: str
    description: Optional[str]
    priority: Priority
    tags: List[Tag]
    assignee_ids: List[str]
    metadata: List[Metadata]
    is_active: bool
    estimated_hours: Optional[float]


@strawberry.type
class BulkTaskResult:
    created_tasks: List[Task]
    total_count: int
    success: bool


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_task(self, input: TaskInput) -> Task:
        """Create a task with complex nested inputs."""
        tags = []
        if input.tags:
            for i, tag_input in enumerate(input.tags):
                metadata = []
                if tag_input.metadata:
                    metadata = [
                        Metadata(key=m.key, value=m.value) for m in tag_input.metadata
                    ]
                tags.append(
                    Tag(
                        id=f"tag-{i}",
                        name=tag_input.name,
                        color=tag_input.color,
                        metadata=metadata,
                    )
                )

        metadata = []
        if input.metadata:
            metadata = [Metadata(key=m.key, value=m.value) for m in input.metadata]

        return Task(
            id="task-1",
            title=input.title,
            description=input.description,
            priority=input.priority,
            tags=tags,
            assignee_ids=input.assignee_ids or [],
            metadata=metadata,
            is_active=input.is_active,
            estimated_hours=input.estimated_hours,
        )

    @strawberry.mutation
    def create_bulk_tasks(self, input: BulkTaskInput) -> BulkTaskResult:
        """Create multiple tasks at once."""
        created_tasks = []

        for i, task_input in enumerate(input.tasks):
            # Override priority if default is set
            if input.default_priority and task_input.priority == Priority.MEDIUM:
                task_input.priority = input.default_priority

            task = Task(
                id=f"bulk-task-{i}",
                title=task_input.title,
                description=task_input.description,
                priority=task_input.priority,
                tags=[],
                assignee_ids=task_input.assignee_ids or [],
                metadata=[],
                is_active=task_input.is_active,
                estimated_hours=task_input.estimated_hours,
            )
            created_tasks.append(task)

        return BulkTaskResult(
            created_tasks=created_tasks, total_count=len(created_tasks), success=True
        )


@strawberry.type
class Query:
    @strawberry.field
    def dummy(self) -> str:
        return "dummy"


def test_enum_input():
    """Test enum values in input."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateTask($input: TaskInput!) {
        createTask(input: $input) {
            id
            title
            priority
        }
    }
    """

    variables = {"input": {"title": "Urgent Task", "priority": "URGENT"}}

    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["createTask"]["title"] == "Urgent Task"
    assert result["createTask"]["priority"] == "URGENT"

    print("✅ Enum input works")


def test_deeply_nested_input():
    """Test deeply nested input objects."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateComplexTask($input: TaskInput!) {
        createTask(input: $input) {
            id
            title
            tags {
                name
                color
                metadata {
                    key
                    value
                }
            }
            metadata {
                key
                value
            }
        }
    }
    """

    variables = {
        "input": {
            "title": "Complex Task",
            "tags": [
                {
                    "name": "frontend",
                    "color": "blue",
                    "metadata": [
                        {"key": "framework", "value": "react"},
                        {"key": "version", "value": "18"},
                    ],
                },
                {
                    "name": "backend",
                    "color": "green",
                    "metadata": [{"key": "language", "value": "python"}],
                },
            ],
            "metadata": [
                {"key": "project", "value": "strawberry"},
                {"key": "sprint", "value": "42"},
            ],
        }
    }

    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["createTask"]["title"] == "Complex Task"
    assert len(result["createTask"]["tags"]) == 2
    assert result["createTask"]["tags"][0]["name"] == "frontend"
    assert result["createTask"]["tags"][0]["metadata"][0]["key"] == "framework"
    assert result["createTask"]["tags"][0]["metadata"][0]["value"] == "react"
    assert len(result["createTask"]["metadata"]) == 2
    assert result["createTask"]["metadata"][1]["value"] == "42"

    print("✅ Deeply nested input works")


def test_list_of_input_objects():
    """Test list of input objects."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateBulkTasks($input: BulkTaskInput!) {
        createBulkTasks(input: $input) {
            createdTasks {
                id
                title
                priority
            }
            totalCount
            success
        }
    }
    """

    variables = {
        "input": {
            "tasks": [
                {"title": "Task 1", "priority": "HIGH"},
                {"title": "Task 2", "priority": "LOW"},
                {"title": "Task 3"},  # Should use default MEDIUM
            ],
            "defaultPriority": "URGENT",
            "autoAssign": True,
        }
    }

    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["createBulkTasks"]["totalCount"] == 3
    assert result["createBulkTasks"]["success"] is True
    assert result["createBulkTasks"]["createdTasks"][0]["priority"] == "HIGH"
    assert (
        result["createBulkTasks"]["createdTasks"][2]["priority"] == "URGENT"
    )  # Default applied

    print("✅ List of input objects works")


def test_boolean_and_float_inputs():
    """Test boolean and float input fields."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateTask($input: TaskInput!) {
        createTask(input: $input) {
            title
            isActive
            estimatedHours
        }
    }
    """

    variables = {
        "input": {"title": "Test Task", "isActive": False, "estimatedHours": 3.5}
    }

    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["createTask"]["isActive"] is False
    assert result["createTask"]["estimatedHours"] == 3.5

    print("✅ Boolean and float inputs work")


def test_null_vs_undefined_inputs():
    """Test null vs undefined (missing) input fields."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateTask($title: String!, $description: String) {
        createTask(input: {title: $title, description: $description}) {
            title
            description
        }
    }
    """

    # Test with null description
    variables = {"title": "Task with null description", "description": None}

    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["createTask"]["title"] == "Task with null description"
    assert result["createTask"]["description"] is None

    # Test with undefined description (not in variables)
    variables = {"title": "Task with undefined description"}

    result = compiled_fn(Mutation(), variables=variables)
    assert result["createTask"]["title"] == "Task with undefined description"
    assert result["createTask"]["description"] is None

    print("✅ Null vs undefined inputs work")


def test_mixed_inline_and_variable_inputs():
    """Test mixing inline and variable inputs."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateTask($title: String!, $tags: [TagInput!]) {
        createTask(input: {
            title: $title,
            priority: HIGH,
            isActive: true,
            tags: $tags,
            estimatedHours: 5.0
        }) {
            title
            priority
            isActive
            tags {
                name
            }
            estimatedHours
        }
    }
    """

    variables = {
        "title": "Mixed Input Task",
        "tags": [{"name": "important"}, {"name": "review"}],
    }

    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["createTask"]["title"] == "Mixed Input Task"
    assert result["createTask"]["priority"] == "HIGH"
    assert result["createTask"]["isActive"] is True
    assert len(result["createTask"]["tags"]) == 2
    assert result["createTask"]["estimatedHours"] == 5.0

    print("✅ Mixed inline and variable inputs work")


def test_empty_list_inputs():
    """Test empty list inputs."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateTask($input: TaskInput!) {
        createTask(input: $input) {
            title
            tags {
                name
            }
            assigneeIds
        }
    }
    """

    variables = {
        "input": {"title": "Task with empty lists", "tags": [], "assigneeIds": []}
    }

    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["createTask"]["title"] == "Task with empty lists"
    assert result["createTask"]["tags"] == []
    assert result["createTask"]["assigneeIds"] == []

    print("✅ Empty list inputs work")


def test_input_validation_performance():
    """Test performance with complex input validation."""
    import time

    from graphql import execute_sync, parse

    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateTask($input: TaskInput!) {
        createTask(input: $input) {
            id
            title
            priority
            tags {
                name
                metadata {
                    key
                    value
                }
            }
        }
    }
    """

    variables = {
        "input": {
            "title": "Performance Test Task",
            "priority": "HIGH",
            "tags": [
                {
                    "name": f"tag-{i}",
                    "metadata": [
                        {"key": f"key-{j}", "value": f"value-{j}"} for j in range(3)
                    ],
                }
                for i in range(5)
            ],
        }
    }

    root = Mutation()
    iterations = 100

    # Standard execution
    start = time.perf_counter()
    for _ in range(iterations):
        result = execute_sync(
            schema._schema, parse(query), root_value=root, variable_values=variables
        )
    standard_time = time.perf_counter() - start

    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    start = time.perf_counter()
    for _ in range(iterations):
        result = compiled_fn(root, variables=variables)
    jit_time = time.perf_counter() - start

    speedup = standard_time / jit_time
    print(f"✅ Complex input performance: {speedup:.2f}x faster with JIT")
    # JIT should provide measurable speedup, but exact amount varies by system
    assert speedup > 1.0, "JIT should be faster than standard execution"


if __name__ == "__main__":
    test_enum_input()
    test_deeply_nested_input()
    test_list_of_input_objects()
    test_boolean_and_float_inputs()
    test_null_vs_undefined_inputs()
    test_mixed_inline_and_variable_inputs()
    test_empty_list_inputs()
    test_input_validation_performance()

    print("\n✅ All input edge case tests passed!")
