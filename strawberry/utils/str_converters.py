# from .ctx import auto_camelcase

class Converter:
    # Adapted from this response in Stackoverflow
    # http://stackoverflow.com/a/19053800/1072990
    def __call__(self, snake_str: str) -> str:
        components = snake_str.split("_")
        # We capitalize the first letter of each component except the first one
        # with the 'capitalize' method and join them together.
        return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])

    def default_call(self, snake_str: str) -> str:
        return snake_str

def capitalize_first(name: str) -> str:
    return name[0].upper() + name[1:]

to_camel_case = Converter()
