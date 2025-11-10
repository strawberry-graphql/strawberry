Release type: patch

Removed `Transfer-Encoding: chunked` header from multipart streaming responses. This fixes HTTP 405 errors on Vercel and other serverless platforms. The server/gateway will handle chunked encoding automatically when needed.
