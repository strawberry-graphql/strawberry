Release type: patch

Fix bug #1504 in the Pydantic integration, where it was impossible to define
both an input and output type based on the same Pydantic base class.
