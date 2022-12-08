Release type: minor

This release changes the `get_context`, `get_root_value` and `process_result`
methods of the Flask async view to be async functions. This allows you to use
async code in these methods.
