Release type: minor

This release updates get_context in the django integration to also receive a temporal response object that can be used to set headers, cookies and status code.


```
@strawberry.type
class Query:
    @strawberry.field
    def abc(self, info: Info) -> str:
        info.context.response.status_code = 418

        return "ABC"
```
