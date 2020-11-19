Release type: minor

Creation of a `[debug-server]` extra, which is required to get going quickly with this project!

```
pip install strawberry-graphql
```

Will now install the primary portion of of the framework, allowing you to build your GraphQL
schema using the dataclasses pattern.

To get going quickly, you can install `[debug-server]` which brings along a server which allows
you to develop your API dynamically, assuming your schema is defined in the `app` module:

```
pip install strawberry-graphql[debug-server]
strawberry server app
```

Typically, in a production environment, you'd want to bring your own server :)
