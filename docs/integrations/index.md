# integrations

WIP:

| name                        | Supports sync | Supports async       | Supports subscriptions via websockets | Supports subscriptions via multipart HTTP | Supports file uploads | Supports batch queries |
| --------------------------- | ------------- | -------------------- | ------------------------------------- | ----------------------------------------- | --------------------- | ---------------------- |
| [django](//django.md)       | ✅            | ✅ (with Async view) | ❌ (use Channels for websockets)      | ✅ (From Django 4.2)                      | ✅                    | ❌                     |
| [starlette](//starlette.md) | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
| [aiohttp](//aiohttp.md)     | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
| [flask](//flask.md)         | ✅            | ✅                   | ❌                                    | ❌                                        | ✅                    | ✅                     |
| [channels](//channels.md)   | ✅            | ✅                   | ✅                                    | ❌                                        | ✅                    | ✅                     |
| [fastapi](//fastapi.md)     | ✅            | ✅                   | ✅                                    | ✅                                        | ✅                    | ✅                     |
