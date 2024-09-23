Release type: minor

Starting with this release, multipart uploads are disabled by default and Strawberry Django view is no longer implicitly exempted from Django's CSRF protection.
Both changes relieve users from implicit security implications inherited from the GraphQL multipart request specification which was enabled in Strawberry by default.

These are breaking changes if you are using multipart uploads OR the Strawberry Django view.
Migrations guides including further information are available on the Strawberry website.
