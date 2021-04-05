Release type: minor

Add --app-dir CLI option to specify where to find the schema module to load when using
the debug server.

For example if you have a _schema_ module in a _my_app_ package under ./src, then you
can run the debug server with it using:

```bash
strawberry server --app-dir src my_app.schema
```
