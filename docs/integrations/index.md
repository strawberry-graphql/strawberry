# integrations

WIP:

| name                                         | Supports sync | Supports async       | Supports subscriptions via websockets | Supports subscriptions via multipart HTTP | Supports file uploads | Supports batch queries |
| -------------------------------------------- | ------------- | -------------------- | ------------------------------------- | ----------------------------------------- | --------------------- | ---------------------- |
| [django](/docs/integrations/django.md)       | ✅            | ✅ (with Async view) | ❌ (use Channels for websockets)      | ✅                                        | ✅                    | ❌                     |
| [starlette](/docs/integrations/starlette.md) | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
| [aiohttp](/docs/integrations/aiohttp.md)     | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
| [flask](/docs/integrations/flask.md)         | ✅            | ✅                   | ❌                                    | ❌                                        | ✅                    | ✅                     |
| [channels](/docs/integrations/channels.md)   | ✅            | ✅                   | ✅                                    | ❌                                        | ✅                    | ✅                     |
| [fastapi](/docs/integrations/fastapi.md)     | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
