#!/bin/bash

# Script to fix JIT test assertions to use wrapped data format

files=(
    "tests/jit/test_mutations.py"
    "tests/jit/test_jit_arguments.py"
    "tests/jit/test_jit_async.py"
    "tests/jit/test_jit_benchmark.py"
    "tests/jit/test_union_types.py"
    "tests/jit/test_jit_fragments_optimized.py"
    "tests/jit/test_type_map_performance.py"
)

for file in "${files[@]}"; do
    echo "Fixing $file..."

    # Add import if not present
    if ! grep -q "assert_jit_results_match" "$file"; then
        sed -i '' '/from strawberry.jit import compile_query/a\
from tests.jit.conftest import assert_jit_results_match
' "$file"
    fi

    # Replace standard assertion patterns
    sed -i '' 's/assert jit_result == standard_result\.data/assert_jit_results_match(jit_result, standard_result)/g' "$file"
    sed -i '' 's/assert jit_result == result\.data/assert_jit_results_match(jit_result, result)/g' "$file"

done

echo "Done!"
