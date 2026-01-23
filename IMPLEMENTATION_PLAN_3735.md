# Implementation Plan: Type-Level Permissions (Issue #3735)

## Overview

This plan details the implementation of permission checks at the type level for Strawberry GraphQL, following **Option 1** from the issue discussion.

### Proposed API

```python
@strawberry.type(permission_classes=[AdminOnly, CurrentUser])
class User:
    id: strawberry.ID
    email: str
```

**How it works:** When any field resolves to a `User` type, the permission checks run **after resolution** (post-resolution). This differs from field-level permissions which check **before resolution**.

---

## 1. API Changes

### 1.1 Modify `@strawberry.type` Decorator

**File:** `strawberry/types/object_type.py` (lines 191-310)

Add `permission_classes` parameter to both overloads and main implementation:

```python
@overload
def type(
    cls: T,
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
    permission_classes: list[type[BasePermission]] | None = None,  # NEW
) -> T: ...

@overload
def type(
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
    permission_classes: list[type[BasePermission]] | None = None,  # NEW
) -> Callable[[T], T]: ...

def type(
    cls: T | None = None,
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
    permission_classes: list[type[BasePermission]] | None = None,  # NEW
) -> T | Callable[[T], T]:
```

### 1.2 Update `_process_type()` Function

**File:** `strawberry/types/object_type.py` (lines 123-188)

```python
def _process_type(
    cls: T,
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
    original_type_annotations: dict[str, Any] | None = None,
    permission_classes: list[type[BasePermission]] | None = None,  # NEW
) -> T:
    # ... existing code ...

    # Add validation: input types cannot have permissions
    if is_input and permission_classes:
        raise ValueError("Input types cannot have permission_classes")

    cls.__strawberry_definition__ = StrawberryObjectDefinition(
        # ... existing params ...
        permission_classes=permission_classes or [],  # NEW
    )
```

### 1.3 Update `@strawberry.interface` (Optional)

**File:** `strawberry/types/object_type.py` (lines 420-462)

For consistency, add `permission_classes` to interfaces. However, the actual checks will apply to concrete implementing types at runtime.

---

## 2. Data Model Changes

### 2.1 Add `permission_classes` to `StrawberryObjectDefinition`

**File:** `strawberry/types/base.py` (lines 261-287)

```python
@dataclasses.dataclass(eq=False)
class StrawberryObjectDefinition(StrawberryType):
    name: str
    is_input: bool
    is_interface: bool
    origin: type[Any]
    description: str | None
    interfaces: list[StrawberryObjectDefinition]
    extend: bool
    directives: Sequence[object] | None
    is_type_of: Callable[[Any, GraphQLResolveInfo], bool] | None
    resolve_type: Callable[[Any, GraphQLResolveInfo, GraphQLAbstractType], str] | None
    fields: list[StrawberryField]
    permission_classes: list[type[BasePermission]] = dataclasses.field(default_factory=list)  # NEW
```

### 2.2 Update `copy_with()` Method

**File:** `strawberry/types/base.py` (lines 312-347)

Preserve `permission_classes` when creating generic type copies:

```python
def copy_with(
    self, type_var_map: Mapping[str, StrawberryType | type]
) -> type[WithStrawberryObjectDefinition]:
    # ... existing code ...

    new_type_definition = StrawberryObjectDefinition(
        # ... existing params ...
        permission_classes=self.permission_classes[:],  # NEW - copy the list
    )
```

---

## 3. Core Permission Checking Implementation

### 3.1 Add Helper Functions to `permission.py`

**File:** `strawberry/permission.py`

```python
def get_type_permission_classes(
    field_type: StrawberryType | type,
) -> list[type[BasePermission]]:
    """Extract permission classes from a field's return type.

    Handles:
    - Direct types: User -> User's permission_classes
    - Optional types: Optional[User] -> User's permission_classes
    - List types: List[User] -> User's permission_classes
    - Unions: Handled at runtime based on resolved type
    """
    from strawberry.types.base import (
        StrawberryList,
        StrawberryOptional,
        has_object_definition,
        get_object_definition,
    )
    from strawberry.types.union import StrawberryUnion

    # Unwrap containers to get the inner type
    inner_type = field_type
    while isinstance(inner_type, (StrawberryOptional, StrawberryList)):
        inner_type = inner_type.of_type

    # For unions, permissions are checked at runtime
    if isinstance(inner_type, StrawberryUnion):
        return []

    # Get permissions from the type definition
    if has_object_definition(inner_type):
        type_def = get_object_definition(inner_type)
        if type_def and hasattr(type_def, 'permission_classes'):
            return type_def.permission_classes

    return []


def get_permissions_from_resolved_value(value: Any) -> list[type[BasePermission]]:
    """Get permission classes from the actual resolved value's type."""
    from strawberry.types.base import has_object_definition, get_object_definition

    if value is None:
        return []

    value_type = type(value)
    if has_object_definition(value_type):
        type_def = get_object_definition(value_type)
        if type_def and hasattr(type_def, 'permission_classes'):
            return type_def.permission_classes

    return []
```

### 3.2 Modify `from_resolver()` in Schema Converter

**File:** `strawberry/schema/schema_converter.py` (lines 689-801)

This is the critical change. Wrap resolver results to check type permissions:

```python
def from_resolver(
    self, field: StrawberryField
) -> Callable:
    # ... existing code up to _get_result_with_extensions ...

    _get_result_with_extensions = wrap_field_extensions()

    # NEW: Get type permissions for this field's return type
    type_permission_classes = self._get_type_permissions_for_field(field)

    def _resolver(_source: Any, info: GraphQLResolveInfo, **kwargs: Any) -> Any:
        strawberry_info = _strawberry_info_from_graphql(info)

        result = _get_result_with_extensions(
            _source,
            strawberry_info,
            **kwargs,
        )

        # NEW: Check type permissions on resolved value
        if type_permission_classes:
            result = self._check_type_permissions_sync(
                result, strawberry_info, type_permission_classes, field
            )

        return result

    async def _async_resolver(
        _source: Any, info: GraphQLResolveInfo, **kwargs: Any
    ) -> Any:
        strawberry_info = _strawberry_info_from_graphql(info)

        result = await await_maybe(
            _get_result_with_extensions(
                _source,
                strawberry_info,
                **kwargs,
            )
        )

        # NEW: Check type permissions on resolved value (async)
        if type_permission_classes:
            result = await self._check_type_permissions_async(
                result, strawberry_info, type_permission_classes, field
            )

        return result

    # ... rest of method ...
```

### 3.3 Add Helper Methods to `GraphQLCoreConverter`

**File:** `strawberry/schema/schema_converter.py`

```python
def _get_type_permissions_for_field(
    self, field: StrawberryField
) -> list[type[BasePermission]] | None:
    """Get permission classes from field's return type."""
    from strawberry.permission import get_type_permission_classes

    permissions = get_type_permission_classes(field.type)
    return permissions if permissions else None


def _check_type_permissions_sync(
    self,
    result: Any,
    info: Info,
    permission_classes: list[type[BasePermission]],
    field: StrawberryField,
) -> Any:
    """Check permissions on resolved value (sync)."""
    if result is None:
        return result

    # Handle list types - check each item
    if isinstance(result, (list, tuple)):
        checked_items = []
        for item in result:
            checked = self._check_single_value_permissions_sync(
                item, info, permission_classes, field
            )
            if checked is not None:  # Filter out unauthorized items
                checked_items.append(checked)
        return checked_items

    return self._check_single_value_permissions_sync(
        result, info, permission_classes, field
    )


def _check_single_value_permissions_sync(
    self,
    value: Any,
    info: Info,
    static_permissions: list[type[BasePermission]],
    field: StrawberryField,
) -> Any:
    """Check permissions on a single resolved value (sync)."""
    from strawberry.permission import get_permissions_from_resolved_value
    from strawberry.types.base import StrawberryOptional

    if value is None:
        return value

    # Get runtime permissions (handles unions/polymorphism)
    runtime_permissions = get_permissions_from_resolved_value(value)
    permissions_to_check = runtime_permissions or static_permissions

    for permission_class in permissions_to_check:
        permission = permission_class()
        if not permission.has_permission(value, info):
            # Return None for optional fields instead of raising
            if isinstance(field.type, StrawberryOptional):
                return None
            permission.on_unauthorized()

    return value


async def _check_type_permissions_async(
    self,
    result: Any,
    info: Info,
    permission_classes: list[type[BasePermission]],
    field: StrawberryField,
) -> Any:
    """Check permissions on resolved value (async)."""
    # Similar structure to sync, but awaits permission checks
    if result is None:
        return result

    if isinstance(result, (list, tuple)):
        checked_items = []
        for item in result:
            checked = await self._check_single_value_permissions_async(
                item, info, permission_classes, field
            )
            if checked is not None:
                checked_items.append(checked)
        return checked_items

    return await self._check_single_value_permissions_async(
        result, info, permission_classes, field
    )


async def _check_single_value_permissions_async(
    self,
    value: Any,
    info: Info,
    static_permissions: list[type[BasePermission]],
    field: StrawberryField,
) -> Any:
    """Check permissions on a single resolved value (async)."""
    from strawberry.permission import get_permissions_from_resolved_value
    from strawberry.types.base import StrawberryOptional
    from strawberry.utils.await_maybe import await_maybe

    if value is None:
        return value

    runtime_permissions = get_permissions_from_resolved_value(value)
    permissions_to_check = runtime_permissions or static_permissions

    for permission_class in permissions_to_check:
        permission = permission_class()
        has_permission = await await_maybe(
            permission.has_permission(value, info)
        )
        if not has_permission:
            if isinstance(field.type, StrawberryOptional):
                return None
            permission.on_unauthorized()

    return value
```

---

## 4. Type Resolution Flow

### 4.1 Direct Returns (`User`)

```
Query: { user { id } }
Flow:
1. Resolver executes → returns User instance
2. Type permissions checked on User instance
3. Success → return User for field resolution
4. Failure → raise error
```

### 4.2 Optional Types (`Optional[User]`)

```
Query: { user { id } }  # where user: Optional[User]
Flow:
1. Resolver executes
2. If result is None → return None (skip permission check)
3. If result is User → check permissions
4. On failure → return None (instead of error)
```

### 4.3 List Types (`List[User]`)

```
Query: { users { id } }
Flow:
1. Resolver executes → returns [User1, User2, User3]
2. For each User → check permissions
3. Filter out unauthorized items (return [User1, User3] if User2 fails)
```

### 4.4 Nested Types

```
Query: { user { address { street } } }
Flow:
1. user field resolved → User permissions checked
2. address field resolved → Address permissions checked (if Address has permissions)
Each nested type gets its own permission check via its own resolver
```

### 4.5 Unions

```python
SearchResult = Annotated[User | Post, strawberry.union("SearchResult")]

@strawberry.type(permission_classes=[AdminOnly])
class User: ...

@strawberry.type  # No permissions
class Post: ...
```

```
Query: { search { ... on User { email } ... on Post { title } } }
Flow:
1. Resolver returns actual value (User or Post)
2. Permission check uses ACTUAL resolved type
3. User → check AdminOnly; Post → no check
```

### 4.6 Interfaces

```python
@strawberry.interface
class Node:
    id: strawberry.ID

@strawberry.type(permission_classes=[AdminOnly])
class User(Node):
    email: str
```

```
Query: { node { id ... on User { email } } }  # returns Node
Flow:
1. Resolver returns User instance (implementing Node)
2. Permission check uses ACTUAL type (User), not declared type (Node)
3. Check AdminOnly permission
```

---

## 5. Edge Cases

### 5.1 Both Field AND Type Have Permissions

**Behavior:** Both are checked sequentially.

```python
@strawberry.type(permission_classes=[TypePermission])  # Checked 2nd (post-resolution)
class User: ...

@strawberry.type
class Query:
    @strawberry.field(permission_classes=[FieldPermission])  # Checked 1st (pre-resolution)
    def user(self) -> User: ...
```

Execution order:
1. FieldPermission checked (BEFORE resolution)
2. Resolver executes
3. TypePermission checked (AFTER resolution)

### 5.2 Same Type Returned Multiple Times

**Behavior:** Check permissions each time.

```python
@strawberry.type
class Query:
    def user(self) -> User: ...      # Permissions checked
    def admin(self) -> User: ...     # Permissions checked again
    def users(self) -> list[User]:   # Permissions checked per item
```

Rationale: The source/context may differ.

### 5.3 Input Types

**Behavior:** Error if `permission_classes` provided.

```python
@strawberry.input(permission_classes=[...])  # Raises ValueError
class UserInput: ...
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**File:** `tests/schema/test_type_permissions.py` (new)

```python
def test_type_permission_basic():
    """Type with permission_classes denies unauthorized access"""

def test_type_permission_allows_authorized():
    """Type permissions pass when has_permission returns True"""

def test_type_permission_optional_field_returns_none():
    """Optional field returns None when type permission fails"""

def test_type_permission_list_filters_unauthorized():
    """List field filters out unauthorized items"""

def test_type_permission_nested_types():
    """Nested types each get permission checks"""

def test_type_permission_combined_with_field_permission():
    """Both field and type permissions are checked in order"""

def test_type_permission_union_uses_runtime_type():
    """Union types check permissions based on resolved type"""

def test_type_permission_interface_implementation():
    """Interface implementations check concrete type permissions"""

def test_type_permission_async_permission_class():
    """Async permission has_permission works correctly"""

def test_type_permission_async_resolver():
    """Async resolvers with type permissions work correctly"""

def test_type_permission_custom_error():
    """Custom error_class and error_extensions work"""

def test_type_permission_source_is_resolved_value():
    """Permission's source parameter is the resolved value"""

def test_input_type_cannot_have_permissions():
    """Input types raise error if permission_classes provided"""

def test_type_permission_generic_types_preserved():
    """Generic types preserve permission_classes through copy_with"""
```

---

## 7. Files to Modify Summary

| File | Changes |
|------|---------|
| `strawberry/types/base.py` | Add `permission_classes` field to `StrawberryObjectDefinition`, update `copy_with()` |
| `strawberry/types/object_type.py` | Add `permission_classes` param to `type()`, `_process_type()`, `interface()` |
| `strawberry/permission.py` | Add `get_type_permission_classes()` and `get_permissions_from_resolved_value()` helpers |
| `strawberry/schema/schema_converter.py` | Modify `from_resolver()`, add `_check_type_permissions_*` methods |
| `tests/schema/test_type_permissions.py` | New test file |
| `docs/guides/permissions.md` | Document type-level permissions |

---

## 8. Implementation Order

1. **Phase 1: Data Model**
   - Add `permission_classes` to `StrawberryObjectDefinition`
   - Update `copy_with()` method

2. **Phase 2: API**
   - Update `@strawberry.type` decorator
   - Update `_process_type()`
   - Add input type validation

3. **Phase 3: Core Logic**
   - Add helper functions to `permission.py`
   - Modify `from_resolver()` in schema converter
   - Add permission checking methods

4. **Phase 4: Testing**
   - Write comprehensive unit tests
   - Test edge cases

5. **Phase 5: Documentation**
   - Update permissions guide
   - Add examples
