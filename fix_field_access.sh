#!/bin/bash

# Fix field access patterns in test files
files=(
    "tests/jit/test_jit_async.py"
    "tests/jit/test_jit_arguments.py"
    "tests/jit/test_mutations.py"
)

for file in "${files[@]}"; do
    echo "Fixing field access in $file..."

    # Replace jit_result["field"] with jit_result["data"]["field"]
    # But not if it already has ["data"]

    # Use perl for more complex regex
    perl -i -pe 's/jit_result\[("(?:posts|users|hello|post|search|asyncPosts|asyncHello|asyncUsers|createUser|updatePost|deletePost)"])/jit_result["data"][$1/g unless /jit_result\["data"\]/' "$file"

done

echo "Done!"
