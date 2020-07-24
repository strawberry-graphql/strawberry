# TODO: support for this

# def test_query_interface():
#     """Test that a query on an interface correctly detects instances of the dataclasses
#        as one of the inherited types, given that types
#        are registered in addition to the
#        root type (since there is no field for them)"""

#     @strawberry.interface
#     class Cheese:
#         name: str

#     @strawberry.type
#     class Swiss(Cheese):
#         canton: str

#     @strawberry.type
#     class Italian(Cheese):
#         province: str

#     @strawberry.type
#     class Root:
#         @strawberry.field
#         def assortment(self, info) -> typing.List[Cheese]:
#             return [
#                 Italian(name="Asiago", province="Friuli"),
#                 Swiss(name="Tomme", canton="Vaud"),
#             ]

#     schema = strawberry.Schema(query=Root, types=[Swiss, Italian])

#     query = """{
#         assortment {
#             name
#             ... on Italian { province }
#             ... on Swiss { canton }
#         }
#     }"""

#     result = schema.execute_sync(query)

#     assert not result.errors
#     assert result.data["assortment"] == [
#         {"name": "Asiago", "province": "Friuli"},
#         {"canton": "Vaud", "name": "Tomme"},
#     ]
