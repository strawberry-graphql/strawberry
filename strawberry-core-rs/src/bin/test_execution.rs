/// Test apollo-compiler's execution capabilities
use apollo_compiler::{Schema, ExecutableDocument};
use apollo_compiler::resolvers::{Execution, ObjectValue, ResolvedValue, ResolveInfo, FieldError};

struct QueryResolver;
impl ObjectValue for QueryResolver {
    fn type_name(&self) -> &str { "Query" }

    fn resolve_field<'a>(&'a self, info: &'a ResolveInfo<'a>) -> Result<ResolvedValue<'a>, FieldError> {
        match info.field_name() {
            "hello" => Ok(ResolvedValue::leaf("Hello from Rust!")),
            "stadium" => Ok(ResolvedValue::object(StadiumResolver)),
            _ => Err(self.unknown_field_error(info)),
        }
    }
}

struct StadiumResolver;
impl ObjectValue for StadiumResolver {
    fn type_name(&self) -> &str { "Stadium" }

    fn resolve_field<'a>(&'a self, info: &'a ResolveInfo<'a>) -> Result<ResolvedValue<'a>, FieldError> {
        match info.field_name() {
            "name" => Ok(ResolvedValue::leaf("Grand Metropolitan Stadium")),
            "city" => Ok(ResolvedValue::leaf("London")),
            _ => Err(self.unknown_field_error(info)),
        }
    }
}

fn main() {
    println!("Testing apollo-compiler execution...\n");

    let schema_sdl = r#"
        type Query { hello: String stadium: Stadium }
        type Stadium { name: String! city: String! }
    "#;

    let schema = Schema::parse(schema_sdl, "schema.graphql").unwrap().validate().unwrap();
    println!("✅ Schema validated");

    let query = "{ hello stadium { name city } }";
    let document = ExecutableDocument::parse(&schema, query, "query.graphql").unwrap();
    println!("✅ Query parsed");

    let document = document.validate(&schema).unwrap();
    println!("✅ Query validated");

    println!("\n🚀 Executing with apollo-compiler...\n");
    let execution = Execution::new(&schema, &document);

    match execution.execute_sync(&QueryResolver) {
        Ok(response) => {
            println!("🎉 Execution successful!\n");
            println!("Response:");
            println!("{}\n", serde_json::to_string_pretty(&response).unwrap());
            println!("✅ apollo-compiler CAN execute GraphQL queries!");
        }
        Err(e) => eprintln!("❌ Error: {:?}", e),
    }
}
