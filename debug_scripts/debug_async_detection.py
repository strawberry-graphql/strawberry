"""Debug which fields are being detected as async."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from schema import schema  # type: ignore

# Check which fields are async
query_type = schema._schema.query_type

print("Query type fields:")
for field_name, field_def in query_type.fields.items():
    is_async = False

    # Check strawberry-definition
    if hasattr(field_def, "extensions") and field_def.extensions:
        strawberry_field = field_def.extensions.get("strawberry-definition")
        if strawberry_field and hasattr(strawberry_field, "is_async"):
            is_async = strawberry_field.is_async

    # Fallback to runtime check
    if not is_async and field_def.resolve:
        import inspect

        is_async = inspect.iscoroutinefunction(field_def.resolve)

    print(f"  {field_name}: {'ASYNC' if is_async else 'sync'}")

# Check Post type
post_type = schema._schema.type_map.get("Post")
if post_type:
    print("\nPost type fields:")
    for field_name, field_def in post_type.fields.items():
        is_async = False

        if hasattr(field_def, "extensions") and field_def.extensions:
            strawberry_field = field_def.extensions.get("strawberry-definition")
            if strawberry_field and hasattr(strawberry_field, "is_async"):
                is_async = strawberry_field.is_async

        if not is_async and field_def.resolve:
            import inspect

            is_async = inspect.iscoroutinefunction(field_def.resolve)

        print(f"  {field_name}: {'ASYNC' if is_async else 'sync'}")
