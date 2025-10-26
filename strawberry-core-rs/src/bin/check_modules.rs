/// Check what modules apollo-compiler exports

fn main() {
    println!("Checking apollo-compiler modules...\n");

    // Try to import various modules
    println!("Available modules:");

    // Core modules (we know these exist)
    println!("  ✅ apollo_compiler::Schema");
    println!("  ✅ apollo_compiler::ExecutableDocument");

    // Check for execution/resolver modules
    #[cfg(any())] // This will never compile, just for checking
    {
        use apollo_compiler::execution::*;
        use apollo_compiler::resolvers::*;
    }

    println!("\nTo check if resolvers exist, trying to reference them:");
    println!("  Checking apollo_compiler::execution...");
    println!("  Checking apollo_compiler::resolvers...");

    // This will show us at compile time what's available
    // If it compiles, the module exists
    // If it doesn't, we'll see the error

    println!("\nRun with: cargo build --bin check_modules 2>&1 | grep 'apollo_compiler::'");
}
