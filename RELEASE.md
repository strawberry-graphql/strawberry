Release type: patch

Fix bug where files would be converted into io.BytesIO when using the sanic GraphQLView
instead of using the sanic File type
