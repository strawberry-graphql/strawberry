Release type: patch

Fixed multipart subscription header parsing to properly handle optional boundary parameters and quoted subscription spec values. This improves compatibility with different GraphQL clients that may send headers in various formats.

**Key improvements:**

- Made the `boundary=graphql` parameter optional in multipart subscription detection
- Added proper quote stripping for `subscriptionSpec` values (e.g., `subscriptionSpec="1.0"`)
- Enhanced test coverage for different header format scenarios

**Example of supported headers:**

```raw
Accept: multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json
Accept: multipart/mixed;subscriptionSpec="1.0",application/json
```
