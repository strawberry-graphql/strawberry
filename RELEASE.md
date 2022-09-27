Release type: minor

Reduce the number of required dependencies, by marking Pygments and python-multipart as optional. These dependencies are still necessary for some functionality, and so users of that functionality need to ensure they're installed, either explicitly or via an extra:

- Pygments is still necessary when using Strawberry in debug mode, and is included in the `strawberry[debug-server]` extra.
- python-multipart is still necessary when using `strawberry.file_uploads.Upload` with FastAPI or Starlette, and is included in the `strawberry[fastapi]` and `strawberry[asgi]` extras, respectively.

There is now also the `strawberry[cli]` extra to support commands like `strawberry codegen` and `strawberry export-schema`.
