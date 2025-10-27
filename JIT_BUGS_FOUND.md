# JIT Compiler Bugs Found During Battle-Testing

## Critical Bugs

### Bug #1: Non-Null Field Error Propagation Returns Entire Result as None

**Severity:** Critical
**Status:** Found
**Test:** `test_non_null_field_error_propagates_to_parent`

**Expected behavior:**
```python
{"data": None}  # data field is null, but root structure exists
```

**Actual behavior:**
```python
None  # Entire result is None
```

**Impact:** When a non-null field errors and should propagate to its parent, the JIT compiler returns the entire result as `None` instead of wrapping it in `{"data": None}`. This breaks GraphQL spec compliance for error handling.

**GraphQL Spec Reference:** https://spec.graphql.org/October2021/#sec-Handling-Field-Errors
Section: "If the field returns non-null, the field error is further propagated to its parent field."

---

### Bug #2: Deep Non-Null Chain Creates Duplicate Errors

**Severity:** High
**Status:** Found
**Test:** `test_deep_non_null_chain`

**Expected behavior:**
```python
# 1 error at the deepest level
{"level1": {"level2": {"level3": None}}}
errors: 1 error with path ['level1', 'level2', 'level3', 'level4', 'level5', 'value']
```

**Actual behavior:**
```python
# 3 errors generated during propagation
{"level1": {"level2": {"level3": None}}}
errors: 3 errors at different levels
```

**Impact:** The JIT compiler generates multiple error entries as the error propagates up the chain, instead of just one error with the full path. This clutters the error response and doesn't match standard GraphQL execution.

---

### Bug #3: Non-Null List Error Returns Entire Result as None

**Severity:** Critical
**Status:** Found
**Test:** `test_non_null_list_with_error`

**Expected behavior:**
```python
{"items": None}  # Root structure exists
```

**Actual behavior:**
```python
None  # Entire result is None
```

**Impact:** Similar to Bug #1, but for lists. When a non-null field in a list item errors, the entire result becomes `None` instead of just the parent field.

---

### Bug #4: Nullable List with Non-Null Items Creates Duplicate Errors

**Severity:** Medium
**Status:** Found
**Test:** `test_nullable_list_with_non_null_items`

**Expected behavior:**
```python
errors: 1 error (from first item that failed)
```

**Actual behavior:**
```python
errors: 2 errors (one from item, one from list level)
```

**Impact:** When processing a list where an item's non-null field errors, the JIT compiler creates duplicate error entries - one for the item and one for the list level. This is incorrect per GraphQL spec.

---

## Root Cause Analysis

### Likely Issue: Error Propagation Logic

The JIT compiler's error handling appears to have issues with:

1. **Result structure preservation** - When propagating errors, the JIT should maintain the `{"data": <result>}` structure, not return raw `None`
2. **Error deduplication** - As errors propagate up the chain, duplicate errors are created instead of preserving the original error with the full path
3. **Non-null constraint handling** - The logic for determining when to null out a field vs propagate to parent may be incorrect

### Code Location

Check `strawberry/jit.py` around lines:
- Error handling in `_generate_field()` (lines 710-720)
- Result construction in `_generate_optimized_function()` (lines 270-280)
- Non-null type checking during field resolution

---

## Test Results Summary

**Passed:** 8/12 tests (66.7%)
**Failed:** 4/12 tests (33.3%)

### Passing Tests
✅ Nullable field returns null
✅ Nullable field error returns null
✅ Non-null list with nullable items
✅ Root level non-null error
✅ Multiple errors collected
✅ Non-null argument with value
✅ Non-null argument with variable
✅ Nullable argument with null

### Failing Tests
❌ Non-null field error propagates to parent
❌ Deep non-null chain
❌ Non-null list with error
❌ Nullable list with non-null items

---

## Recommendations

1. **Fix error propagation logic** - Ensure errors in non-null fields properly propagate to the nearest nullable parent without destroying the result structure
2. **Implement error deduplication** - Only create one error entry per actual error, not multiple as it propagates
3. **Add result wrapper** - Ensure JIT always returns `{"data": <result>, "errors": [...]}` structure
4. **Add more tests** - Continue battle-testing to find additional edge cases

---

---

## List Handling Bugs

### Bug #5: JIT Cannot Handle None Items in Nullable Lists

**Severity:** Critical
**Status:** Found
**Test:** `test_nullable_list_of_nullable_items`, `test_non_null_list_of_nullable_items`

**Expected behavior:**
```python
# For List[Optional[Item]]
{"items": [{"id": 1, "name": "One"}, None, {"id": 3, "name": "Three"}]}
```

**Actual behavior:**
```python
# JIT tries to access .id on None and errors
{"items": None}
errors: "'NoneType' object has no attribute 'id'"
```

**Impact:** The JIT compiler cannot handle `None` items in lists with nullable items. When it encounters a `None` in the list, it tries to resolve fields on it and crashes. This is a fundamental flaw in list processing.

**Root cause:** The JIT doesn't check if list items are `None` before attempting to resolve fields on them. The generated code needs to add null checks for nullable list items.

---

### Bug #6: Duplicate Errors in List Processing

**Severity:** Medium
**Status:** Found
**Test:** `test_nullable_list_of_non_null_items`

**Expected behavior:**
```python
errors: 1 error at the field level
```

**Actual behavior:**
```python
errors: 2 errors (one at field level, one at list level)
```

**Impact:** Similar to Bug #4, the JIT generates duplicate errors when processing lists - once when the field errors, and again when propagating up from the list.

---

### Bug #7: Multiple List Errors Cause Entire Result to be None

**Severity:** Critical
**Status:** Found
**Test:** `test_multiple_errors_in_list`

**Expected behavior:**
```python
# Items are nullable, so errors should null individual items
{"items": [None, None, None]}
errors: 3 errors (one per item)
```

**Actual behavior:**
```python
# Entire result becomes None after first error
None
errors: 2 errors (stops after first)
```

**Impact:** When multiple items in a list have errors in nullable fields, the JIT doesn't continue processing after the first error. It stops execution and nulls the entire result instead of just the individual items.

---

## Test Results Summary

### Non-Null Tests
**Passed:** 8/12 tests (66.7%)
**Failed:** 4/12 tests (33.3%)

### List Tests
**Passed:** 7/11 tests (63.6%)
**Failed:** 4/11 tests (36.4%)

### Overall
**Passed:** 15/23 tests (65.2%)
**Failed:** 8/23 tests (34.8%)

---

## Critical Issues Summary

The JIT compiler has fundamental issues with:

1. ✅ **Result structure** - Sometimes returns `None` instead of `{"data": None}`
2. ❌ **Error propagation** - Creates duplicate errors during propagation
3. ❌ **Null handling in lists** - Cannot handle `None` items in nullable lists
4. ❌ **Multi-error handling** - Stops processing after first error in lists
5. ❌ **Error path tracking** - Generates incorrect error paths

These bugs make the JIT **NOT production-ready** for lists with nullable items or scenarios with multiple errors.

---

---

## Variable Handling Bugs

### Bug #8: JIT Returns Raw Data Instead of {"data": ...} Wrapper

**Severity:** CRITICAL - SYSTEMIC ISSUE
**Status:** Found
**Test:** ALL 17 variable tests failed with same issue

**Expected behavior:**
```python
# Standard GraphQL response format
{"data": {"echo": "Value: hello"}}
```

**Actual behavior:**
```python
# JIT returns unwrapped data
{"echo": "Value: hello"}
```

**Impact:** This is a **SYSTEMIC BUG** affecting ALL JIT queries. The JIT compiler does not return results in the correct GraphQL response format `{"data": <result>, "errors": [...]}`. Instead, it returns the raw data directly. This breaks compatibility with ANY GraphQL client expecting standard response format.

**Test results:**
- **17/17 variable tests failed** (100% failure rate)
- All failures due to missing `{"data": ...}` wrapper
- This affects:
  - Simple queries
  - Queries with variables
  - Queries with default values
  - Complex input objects
  - List variables
  - All variable scenarios

**Root cause:** The `compile_query()` function returns data directly instead of wrapping it in GraphQL response format. This is visible in line 279 of `jit.py`: `return result` should likely be `return {"data": result}`.

---

## Updated Test Results

### Non-Null Tests
**Passed:** 8/12 (66.7%)
**Failed:** 4/12 (33.3%)

### List Tests
**Passed:** 7/11 (63.6%)
**Failed:** 4/11 (36.4%)

### Variable Tests
**Passed:** 0/17 (0%)
**Failed:** 17/17 (100%) - ALL DUE TO BUG #8

### Overall
**Passed:** 15/40 tests (37.5%)
**Failed:** 25/40 tests (62.5%)

---

## CRITICAL FINDING

Bug #8 is a **SHOWSTOPPER** - the JIT compiler's response format is completely incompatible with GraphQL spec. This single bug makes the JIT **COMPLETELY UNUSABLE** in any real-world scenario because:

1. **No GraphQL client will work** - All clients expect `{"data": ...}` format
2. **Error handling is broken** - Errors aren't returned in standard `{"errors": [...]}` format
3. **Federation incompatible** - Gateway/federation tools expect standard format
4. **Tooling incompatible** - GraphiQL, Apollo Studio, etc. won't work

This is not just a test failure - it's a fundamental architectural flaw.

---

## Next Steps

**IMMEDIATE:**
1. **FIX BUG #8 FIRST** - Nothing else matters until response format is correct
2. Re-run ALL tests after fixing Bug #8
3. Verify stadium benchmark with correct format

**AFTER BUG #8 IS FIXED:**
1. Fix Bugs #1, #3, #5, #7 (list/null handling)
2. Continue with abstract type tests
3. Port remaining graphql-core tests

**DO NOT:**
- Use JIT in production
- Recommend JIT to users
- Merge JIT to stable branch
- Document JIT as ready for use
