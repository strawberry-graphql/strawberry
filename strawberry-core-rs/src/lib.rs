/// Strawberry GraphQL execution engine using apollo-compiler
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyAny};
use apollo_compiler::{Schema, ExecutableDocument};
use apollo_compiler::resolvers::{Execution, ObjectValue, ResolvedValue, ResolveInfo, FieldError};
use serde_json::Value as JsonValue;
use std::sync::Arc;

/// Convert camelCase to snake_case
fn camel_to_snake(s: &str) -> String {
    let mut result = String::new();
    for (i, ch) in s.chars().enumerate() {
        if ch.is_uppercase() {
            if i > 0 {
                result.push('_');
            }
            result.push(ch.to_lowercase().next().unwrap());
        } else {
            result.push(ch);
        }
    }
    result
}

struct JsonResolver {
    type_name: String,
    data: JsonValue,
}

impl JsonResolver {
    fn new(type_name: String, data: JsonValue) -> Self {
        Self { type_name, data }
    }
}

impl ObjectValue for JsonResolver {
    fn type_name(&self) -> &str {
        &self.type_name
    }

    fn resolve_field<'a>(&'a self, info: &'a ResolveInfo<'a>) -> Result<ResolvedValue<'a>, FieldError> {
        let field_name = info.field_name();
        let value = match &self.data {
            JsonValue::Object(map) => map.get(field_name),
            _ => None,
        };

        match value {
            Some(JsonValue::String(s)) => Ok(ResolvedValue::leaf(s.clone())),
            Some(JsonValue::Number(n)) => Ok(ResolvedValue::leaf(n.clone())),
            Some(JsonValue::Bool(b)) => Ok(ResolvedValue::leaf(*b)),
            Some(JsonValue::Null) => Ok(ResolvedValue::null()),
            Some(JsonValue::Array(_)) => {
                Ok(ResolvedValue::leaf(value.unwrap().clone()))
            }
            Some(JsonValue::Object(obj)) => {
                // Try to get the type name from __typename field, otherwise infer from schema
                let type_name = obj.get("__typename")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string())
                    .unwrap_or_else(|| {
                        // Infer from field definition
                        let field_def = info.field_definition();
                        field_def.ty.inner_named_type().to_string()
                    });

                Ok(ResolvedValue::object(JsonResolver::new(
                    type_name,
                    value.unwrap().clone(),
                )))
            }
            None => Err(self.unknown_field_error(info)),
        }
    }
}

/// Resolver that calls Python resolver functions
struct PythonResolver {
    type_name: String,
    py_object: PyObject,  // The Python object (e.g., Query instance, Stadium instance)
}

impl PythonResolver {
    fn new(type_name: String, py_object: PyObject) -> Self {
        Self { type_name, py_object }
    }
}

impl ObjectValue for PythonResolver {
    fn type_name(&self) -> &str {
        &self.type_name
    }

    fn resolve_field<'a>(&'a self, info: &'a ResolveInfo<'a>) -> Result<ResolvedValue<'a>, FieldError> {
        let field_name = info.field_name();

        Python::with_gil(|py| {
            let obj = self.py_object.as_ref(py);

            // Try to get the field value/method from the Python object
            // First try the field name as-is (camelCase from GraphQL)
            let result = obj.getattr(field_name)
                .or_else(|_| {
                    // If that fails, try converting to snake_case
                    let snake_case = camel_to_snake(field_name);
                    obj.getattr(snake_case.as_str())
                })
                .map_err(|e| self.unknown_field_error(info))?;

            // Check if it's a method (callable)
            if result.is_callable() {
                // It's a method, we need to call it
                // TODO: Extract arguments from GraphQL query
                let call_result = result.call0()
                    .map_err(|_e| self.unknown_field_error(info))?;

                python_to_resolved_value(py, call_result, info)
            } else {
                // It's a property/attribute, use it directly
                python_to_resolved_value(py, result, info)
            }
        })
    }
}

/// Try to serialize a Python object to JSON for fast processing
fn try_serialize_to_json(py: Python, value: &PyAny) -> Option<JsonValue> {
    // Try dataclasses.asdict first (for Strawberry types)
    if let Ok(dataclasses) = py.import("dataclasses") {
        if let Ok(is_dataclass) = dataclasses.getattr("is_dataclass") {
            if let Ok(result) = is_dataclass.call1((value,)) {
                if let Ok(true) = result.extract::<bool>() {
                    // It's a dataclass! Convert to dict
                    if let Ok(asdict) = dataclasses.getattr("asdict") {
                        if let Ok(dict_result) = asdict.call1((value,)) {
                            // Serialize to JSON
                            if let Ok(json_module) = py.import("json") {
                                if let Ok(dumps) = json_module.getattr("dumps") {
                                    if let Ok(json_str) = dumps.call1((dict_result,)) {
                                        if let Ok(json_str) = json_str.extract::<String>() {
                                            // Parse in Rust
                                            if let Ok(json_val) = serde_json::from_str::<JsonValue>(&json_str) {
                                                return Some(json_val);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    None
}

/// Convert a Python value to a ResolvedValue
fn python_to_resolved_value<'a>(
    py: Python,
    value: &PyAny,
    info: &'a ResolveInfo<'a>,
) -> Result<ResolvedValue<'a>, FieldError> {
    // Check for None
    if value.is_none() {
        return Ok(ResolvedValue::null());
    }

    // Try to extract scalar types
    if let Ok(s) = value.extract::<String>() {
        return Ok(ResolvedValue::leaf(s));
    }

    if let Ok(i) = value.extract::<i64>() {
        return Ok(ResolvedValue::leaf(i));
    }

    if let Ok(f) = value.extract::<f64>() {
        return Ok(ResolvedValue::leaf(f));
    }

    if let Ok(b) = value.extract::<bool>() {
        return Ok(ResolvedValue::leaf(b));
    }

    // Check if it's a list
    if let Ok(list) = value.downcast::<pyo3::types::PyList>() {
        if list.len() == 0 {
            return Ok(ResolvedValue::leaf(JsonValue::Array(vec![])));
        }

        // Convert list items to ResolvedValues one by one
        let mut resolved_items = Vec::new();

        for item in list.iter() {
            // Recursively convert each item
            let resolved = python_to_resolved_value(py, item, info)?;
            resolved_items.push(resolved);
        }

        // Return as a list
        return Ok(ResolvedValue::list(resolved_items.into_iter()));
    }

    // DON'T serialize top-level objects to JSON - apollo-compiler needs resolvers for them
    // Only lists get the JSON optimization

    // Create a PythonResolver for this object
    let type_name = {
        // Try to get __class__.__name__ from the Python object
        if let Ok(class) = value.getattr("__class__") {
            if let Ok(name) = class.getattr("__name__") {
                if let Ok(name_str) = name.extract::<String>() {
                    name_str
                } else {
                    // Fall back to schema inference
                    info.field_definition().ty.inner_named_type().to_string()
                }
            } else {
                info.field_definition().ty.inner_named_type().to_string()
            }
        } else {
            info.field_definition().ty.inner_named_type().to_string()
        }
    };

    // Create a new PythonResolver for this object
    let py_object = value.into();
    Ok(ResolvedValue::object(PythonResolver::new(type_name, py_object)))
}

#[pyfunction]
fn execute_query(schema_sdl: &str, query: &str, root_data: &PyDict) -> PyResult<String> {
    let schema = Schema::parse(schema_sdl, "schema.graphql")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?
        .validate()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?;

    let document = ExecutableDocument::parse(&schema, query, "query.graphql")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?
        .validate(&schema)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?;

    let json_str = Python::with_gil(|py| {
        let json_module = py.import("json")?;
        let dumps = json_module.getattr("dumps")?;
        dumps.call1((root_data,))?.extract::<String>()
    })?;

    let root_value: JsonValue = serde_json::from_str(&json_str)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let resolver = JsonResolver::new("Query".to_string(), root_value);
    let execution = Execution::new(&schema, &document);
    let response = execution.execute_sync(&resolver)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{:?}", e)))?;

    serde_json::to_string_pretty(&response)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

/// Execute a query with Python resolver functions (calls actual resolvers)
#[pyfunction]
fn execute_query_with_resolvers(
    schema_sdl: &str,
    query: &str,
    root_value: PyObject,  // The root Query instance
) -> PyResult<String> {
    let schema = Schema::parse(schema_sdl, "schema.graphql")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?
        .validate()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?;

    let document = ExecutableDocument::parse(&schema, query, "query.graphql")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?
        .validate(&schema)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{:?}", e)))?;

    let resolver = PythonResolver::new("Query".to_string(), root_value);
    let execution = Execution::new(&schema, &document);
    let response = execution.execute_sync(&resolver)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{:?}", e)))?;

    serde_json::to_string_pretty(&response)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

#[pymodule]
fn strawberry_core_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(execute_query, m)?)?;
    m.add_function(wrap_pyfunction!(execute_query_with_resolvers, m)?)?;
    Ok(())
}
