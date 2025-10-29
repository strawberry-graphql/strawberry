# JIT Module Split Implementation Plan

## Status: Ready to Implement

This document provides a detailed, step-by-step plan for splitting `strawberry/jit.py` (2,143 lines) into a well-organized module.

---

## 📊 Proposed Structure

```
strawberry/jit/
├── __init__.py           # Public API exports
├── types.py              # ✅ DONE - MockInfo class
├── utils.py              # ✅ DONE - Utility functions
├── compiler.py           # Main JITCompiler orchestration
├── codegen.py            # Code generation logic
├── introspection.py      # Introspection handling (677 lines!)
└── directives.py         # Directive processing
```

---

## ✅ Already Completed

1. **`jit/types.py`** (30 lines) - MockInfo class
2. **`jit/utils.py`** (220 lines) - sanitize_identifier, serialize_value, CodeEmitter, detect_async_resolvers

---

## 📋 Step-by-Step Implementation

### Step 1: Extract `jit/introspection.py` (Lines 1159-1836)

**Why first:** It's the largest single method (677 lines) and is self-contained.

**Contents:**
- `_generate_introspection_selection()` method → becomes `generate_introspection_selection()` function

**File structure:**
```python
"""Introspection query handling for JIT compiler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import SelectionSetNode, FieldNode

# ... other imports

if TYPE_CHECKING:
    from .compiler import JITCompiler


def generate_introspection_selection(
    compiler: JITCompiler,
    field_name: str,
    parent_var: str,
    result_var: str,
    field: FieldNode,
    selection_set: SelectionSetNode | None,
    info_var: str,
) -> None:
    """Generate code for introspection fields like __schema, __type.

    Args:
        compiler: JITCompiler instance (for access to generated_code, etc.)
        field_name: Name of introspection field
        parent_var: Variable name for parent object
        result_var: Variable name for result
        field: GraphQL field node
        selection_set: Selection set if any
        info_var: Variable name for info object
    """
    # All 677 lines from _generate_introspection_selection
    # Replace self._emit() with compiler._emit()
    # Replace self.type_map with compiler.type_map
    # etc.
```

**Lines to extract:** 1159-1836

---

### Step 2: Extract `jit/directives.py` (Lines 1837-2004)

**Contents:**
- `_generate_abstract_type_selection()` → `generate_abstract_type_selection()`
- `_generate_skip_include_checks()` → `generate_skip_include_checks()`
- `_get_directive_argument()` → `get_directive_argument()`

**File structure:**
```python
"""Directive processing for JIT compiler."""

from __future__ import annotations

from typing import TYPE_CHECKING
from graphql import DirectiveNode, FieldNode, InlineFragmentNode
# ... other imports

if TYPE_CHECKING:
    from .compiler import JITCompiler

def generate_abstract_type_selection(...) -> None:
    """Generate code for union/interface type resolution."""
    # Lines 1837-1973

def generate_skip_include_checks(
    compiler: JITCompiler,
    directives: tuple[DirectiveNode, ...],
    info_var: str
) -> tuple[bool, str]:
    """Generate @skip/@include condition checks."""
    # Lines 1974-1995

def get_directive_argument(directive: DirectiveNode, arg_name: str):
    """Extract argument value from directive."""
    # Lines 1996-2004
```

**Lines to extract:** 1837-2004

---

### Step 3: Extract `jit/codegen.py` (Lines 262-1158)

**Contents:**
- All `_generate_*` methods except introspection and abstract types
- This is the meat of code generation

**Methods to include:**
- `_generate_optimized_function()` (262-364)
- `_is_field_async()` (365-382)
- `_generate_parallel_selection_set()` (383-491)
- `_generate_selection_set()` (492-515)
- `_generate_field()` (516-873) - **LARGEST**
- `_generate_arguments()` (874-900)
- `_generate_argument_value()` (901-1043)
- `_generate_fragment_spread()` (1062-1105)
- `_generate_inline_fragment()` (1106-1158)

**Approach:** Create a `CodeGenerator` class that holds these methods and takes `compiler` as constructor argument.

**File structure:**
```python
"""Code generation logic for JIT compiler."""

from __future__ import annotations

from typing import TYPE_CHECKING
# ... imports

if TYPE_CHECKING:
    from .compiler import JITCompiler

class CodeGenerator:
    """Generates optimized Python code from GraphQL AST."""

    def __init__(self, compiler: JITCompiler):
        self.compiler = compiler

    def generate_optimized_function(self, ...):
        # Lines 262-364

    def is_field_async(self, field_def) -> bool:
        # Lines 365-382

    def generate_parallel_selection_set(self, ...):
        # Lines 383-491

    def generate_selection_set(self, ...):
        # Lines 492-515

    def generate_field(self, ...):
        # Lines 516-873 - THE BIG ONE

    def generate_arguments(self, ...):
        # Lines 874-900

    def generate_argument_value(self, ...):
        # Lines 901-1043

    def generate_fragment_spread(self, ...):
        # Lines 1062-1105

    def generate_inline_fragment(self, ...):
        # Lines 1106-1158

    # Helper to access compiler state
    def _emit(self, line: str):
        self.compiler._emit(line)
```

**Lines to extract:** 262-364, 365-382, 383-491, 492-515, 516-873, 874-900, 901-1043, 1062-1105, 1106-1158

---

### Step 4: Create `jit/compiler.py` (Remaining lines)

**Contents:**
- `JITCompiler` class definition
- `compile_query()` main method
- State management methods
- Public `compile_query()` function

**What stays:**
- Lines 57-95: Class definition and `__init__()`
- Lines 135-238: `compile_query()` method
- Lines 239-261: `_reset_state()`, `_get_operation()`, `_extract_fragments()`
- Lines 2058-2123: `_has_defer_or_stream()` and utilities
- Lines 2124-2143: Public `compile_query()` function

**Imports to add:**
```python
from .types import MockInfo
from .utils import sanitize_identifier, serialize_value, detect_async_resolvers
from .codegen import CodeGenerator
from .introspection import generate_introspection_selection
from .directives import (
    generate_abstract_type_selection,
    generate_skip_include_checks,
    get_directive_argument,
)
```

**File structure:**
```python
"""Main JIT compiler orchestration."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Any

from graphql import (
    DocumentNode,
    OperationDefinitionNode,
    # ... other imports
)

import strawberry

from .types import MockInfo
from .utils import sanitize_identifier, serialize_value, detect_async_resolvers
from .codegen import CodeGenerator
from .introspection import generate_introspection_selection
from .directives import (
    generate_abstract_type_selection,
    generate_skip_include_checks,
    get_directive_argument
)


class JITCompiler:
    """Unified high-performance JIT compiler for GraphQL queries."""

    def __init__(self, schema: strawberry.Schema):
        # Lines 67-95

        # Create helper instances
        self.code_generator = CodeGenerator(self)

    def _sanitize_identifier(self, name: str) -> str:
        """Sanitize identifier - delegate to utils."""
        return sanitize_identifier(name)

    def _serialize_value(self, value) -> str:
        """Serialize value - delegate to utils."""
        return serialize_value(value)

    def compile_query(self, query: str) -> Callable:
        # Lines 135-238
        # Call self.code_generator.generate_optimized_function()

    def _reset_state(self):
        # Lines 239-248

    def _get_operation(self, document: DocumentNode):
        # Lines 249-254

    def _extract_fragments(self, document: DocumentNode):
        # Lines 255-261

    # These get delegated to codegen
    def _generate_optimized_function(self, ...):
        return self.code_generator.generate_optimized_function(...)

    def _generate_field(self, ...):
        return self.code_generator.generate_field(...)

    # ... other delegation methods

    def _emit(self, line: str):
        # Lines 2053-2057 - keep here since state is in compiler

    def _has_defer_or_stream(self, document: DocumentNode) -> bool:
        # Lines 2058-2123


def compile_query(schema: strawberry.Schema, query: str) -> Callable:
    """Compile a GraphQL query into optimized Python code.

    This is the main public API function.
    """
    # Lines 2124-2143
```

---

### Step 5: Create `jit/__init__.py`

**Simple public API:**

```python
"""JIT compiler for Strawberry GraphQL.

Provides compile-time optimizations for GraphQL queries with 5-6x performance improvement.

Example:
    >>> import strawberry
    >>> from strawberry.jit import compile_query
    >>>
    >>> @strawberry.type
    >>> class Query:
    >>>     @strawberry.field
    >>>     def hello(self) -> str:
    >>>         return "world"
    >>>
    >>> schema = strawberry.Schema(query=Query)
    >>> compiled = compile_query(schema, "query { hello }")
    >>> result = compiled(Query())
"""

from .compiler import JITCompiler, compile_query

__all__ = [
    "JITCompiler",
    "compile_query",
]
```

---

### Step 6: Update `strawberry/__init__.py`

**Change:**
```python
# Before
from . import experimental, federation, jit, relay

# After
from . import experimental, federation, relay
from . import jit  # Now imports from jit/__init__.py
```

No other changes needed! The public API stays the same.

---

### Step 7: Keep Backward Compatibility (Optional)

**Create `strawberry/jit.py` as compatibility shim:**

```python
"""
Compatibility shim for old import path.

The JIT compiler has been reorganized into a module. This file
maintains backward compatibility for direct imports.

Deprecated: Import from strawberry.jit instead.
"""

import warnings

# Import everything from new location
from strawberry.jit import *  # noqa: F401, F403
from strawberry.jit import __all__  # noqa: F401

# Warn about deprecated import
warnings.warn(
    "Importing from strawberry.jit as a module is deprecated. "
    "The internal structure has changed but the public API remains the same. "
    "Continue importing from strawberry.jit - no code changes needed.",
    DeprecationWarning,
    stacklevel=2,
)
```

**Then delete in v1.0.**

---

## 🧪 Testing Strategy

After each step, run:

```bash
# Quick smoke test
poetry run python -m pytest tests/jit/test_security.py -v

# Full JIT test suite (slower)
poetry run python -m pytest tests/jit/ -v

# Ensure imports work
poetry run python -c "from strawberry.jit import compile_query; print('✅ Import works')"
```

---

## ⚠️ Potential Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Circular imports** | Use `if TYPE_CHECKING:` and forward references |
| **Shared state** | Pass `compiler` to all helper functions/classes |
| **Method delegation** | Create thin wrapper methods in compiler |
| **`self` references** | Replace with `compiler` parameter |

---

## 📈 Before/After Comparison

| Metric | Before | After | Benefit |
|--------|--------|-------|---------|
| Largest file | 2,143 lines | ~600 lines | ✅ Much more readable |
| Introspection | 677 lines in one method | Separate module | ✅ Isolated concerns |
| Code generation | Mixed with orchestration | Separate module | ✅ Clear responsibility |
| Testability | Hard to unit test | Each module testable | ✅ Better coverage |
| Maintainability | High cognitive load | Focused modules | ✅ Easier to understand |

---

## 🚀 Implementation Time Estimate

- **Step 1** (introspection.py): 30 minutes
- **Step 2** (directives.py): 20 minutes
- **Step 3** (codegen.py): 60 minutes (largest)
- **Step 4** (compiler.py): 40 minutes
- **Step 5** (__init__.py): 5 minutes
- **Step 6** (update imports): 5 minutes
- **Step 7** (testing): 30 minutes

**Total: ~3 hours**

---

## ✅ Success Criteria

1. All existing tests pass
2. No changes to public API
3. Imports work: `from strawberry.jit import compile_query`
4. No performance regression
5. Code is more maintainable

---

## 🎯 Recommendation

**Option A: Do it now** (3 hours)
- Complete the refactoring immediately
- Most thorough and clean
- Same PR as cleanup

**Option B: Separate PR** (recommended)
- Current cleanup PR is already huge (-3,656 lines)
- Split into its own focused PR
- Easier to review
- Less risky

**Option C: Minimal split** (1 hour)
- Just extract introspection.py (677 lines)
- Keep rest in compiler.py
- Still achieves 50% of benefit
- Much safer

---

## My Recommendation: **Option B - Separate PR**

The cleanup we just did is substantial. Let's:
1. ✅ Commit the cleanup (delete 15 redundant files)
2. ✅ Get that reviewed and merged
3. ⏭️ **Then** do the JIT split in a follow-up PR

This approach:
- Keeps PRs focused and reviewable
- Reduces risk
- Allows the cleanup to land quickly
- Gives you fresh eyes for the split

---

## 📝 Next Steps

**If doing now:**
```bash
# I can proceed with the full implementation
# Estimated time: 3 hours
```

**If separate PR:**
```bash
# 1. Commit current cleanup
git add -A
git commit -m "refactor(jit): remove redundant tests and examples

- Delete 12 redundant test files (-3,307 lines)
- Delete 3 redundant example files (-1,328 lines)
- Consolidate security tests into single file
- Move misplaced tests to tests/jit/ directory
- Update examples README with progression guide

Total reduction: 3,656 lines

This cleanup maintains all test coverage while removing duplication
and improving organization."

# 2. Then we can do the split in next PR
```

**What would you like me to do?**
