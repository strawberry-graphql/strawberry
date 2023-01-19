import importlib
from typing import Optional


def import_module_symbol(
    selector: str, default_symbol_name: Optional[str] = None
) -> object:
    if ":" in selector:
        module_name, symbol_name = selector.split(":", 1)
    elif default_symbol_name:
        module_name, symbol_name = selector, default_symbol_name
    else:
        raise ValueError("Selector does not include a symbol name")

    module = importlib.import_module(module_name)
    symbol = module

    for attribute_name in symbol_name.split("."):
        symbol = getattr(symbol, attribute_name)

    return symbol
