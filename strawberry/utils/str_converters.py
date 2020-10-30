auto_camel_case = True
auto_capitalize = True


# Adapted from this response in Stackoverflow
# http://stackoverflow.com/a/19053800/1072990
def to_camel_case(snake_str: str) -> str:
    if auto_camel_case is False:
        return snake_str
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


def capitalize_first(name: str) -> str:
    if auto_capitalize is False:
        return name
    return name[0].upper() + name[1:]
