Release type: minor

`strawberry codegen` can now operate on multiple input query files.
The previous behavior of naming the file `types.js` and `types.py`
for the builtin `typescript` and `python` plugins respectively is
preserved, but only if a single query file is passed.  When more
than one query file is passed, the code generator will now use
the stem of the query file's name to construct the name of the
output files.  e.g. `my_query.graphql` -> `my_query.js` or
`my_query.py`.  Creators of custom plugins are responsible
for controlling the name of the output file themselves.  To
accomodate this, if the `__init__` method of a `QueryCodegenPlugin`
has a parameter named `query` or `query_file`, the `pathlib.Path`
to the query file will be passed to the plugin's `__init__`
method.

Finally, the `ConsolePlugin` has also recieved two new lifecycle
methods.  Unlike other `QueryCodegenPlugin`, the same instance of
the `ConsolePlugin` is used for each query file processed.  This
allows it to keep state around how many total files were processed.
The `ConsolePlugin` recieved two new lifecycle hooks: `before_any_start`
and `after_all_finished` that get called at the appropriate times.
