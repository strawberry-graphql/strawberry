"""Debug: Check what attributes the Query instance has
"""

from test_large_stadium import Query

q = Query()

print("Query instance attributes:")
print(dir(q))
print()

print("Checking for 'stadium':")
print(f"  hasattr(q, 'stadium'): {hasattr(q, 'stadium')}")

if hasattr(q, "stadium"):
    attr = q.stadium
    print(f"  type: {type(attr)}")
    print(f"  callable: {callable(attr)}")
    print(f"  value: {attr}")

print()
print("Try calling it without arguments:")
try:
    result = q.stadium()
    print("  ❌ Should have failed (needs seats_per_row argument)")
except TypeError as e:
    print(f"  ✅ Expected error: {e}")
