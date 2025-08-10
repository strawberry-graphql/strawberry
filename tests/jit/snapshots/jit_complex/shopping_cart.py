#!/usr/bin/env python
"""
Standalone JIT-compiled GraphQL executor.
This file was automatically generated and can be executed independently.

Query Details:
- Operation: query GetShoppingCart
- Root Type: Query
- Top-level Fields: shoppingCart
- Generated: [timestamp]
"""

from typing import Any, Dict, List, Optional
class _MockInfo:
    """Mock GraphQLResolveInfo for JIT execution."""
    def __init__(self, schema):
        self.schema = schema
        self.field_name = None
        self.parent_type = None
        self.return_type = None
        self.path = []
        self.operation = None
        self.variable_values = {}
        self.context = None
        self.root_value = None
        self.fragments = {}


def _default_resolver(obj, info):
    """Default field resolver that gets attributes or dict values."""
    field_name = info.field_name
    if hasattr(obj, field_name):
        return getattr(obj, field_name)
    elif isinstance(obj, dict):
        return obj.get(field_name)
    return None


# Resolver map - will be populated with actual resolvers at runtime
# For standalone execution, these will use the default resolver
_resolvers = {}


def execute_query(root, context=None, variables=None):
    """Execute the JIT-compiled GraphQL query."""
    result = {}
    info = _MockInfo(None)  # Mock info object
    info.root_value = root
    info.context = context
    info.variable_values = variables or {}
    info.field_name = "shoppingCart"
    info.parent_type = "Query"
    resolver = _resolvers['resolver_0']
    field_shoppingCart_value = resolver(root, info)
    if field_shoppingCart_value is not None:
        nested_shoppingCart_result = {}
        info.field_name = "id"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_1']
        field_id_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["id"] = field_id_value
        info.field_name = "itemCount"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_2']
        field_itemCount_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["itemCount"] = field_itemCount_value
        info.field_name = "subtotal"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_3']
        field_subtotal_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["subtotal"] = field_subtotal_value
        info.field_name = "taxAmount"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_4']
        field_taxAmount_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["taxAmount"] = field_taxAmount_value
        info.field_name = "shippingCost"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_5']
        field_shippingCost_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["shippingCost"] = field_shippingCost_value
        info.field_name = "total"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_6']
        field_total_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["total"] = field_total_value
        info.field_name = "totalSavings"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_7']
        field_totalSavings_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["totalSavings"] = field_totalSavings_value
        info.field_name = "freeShippingMessage"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_8']
        field_freeShippingMessage_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["freeShippingMessage"] = field_freeShippingMessage_value
        info.field_name = "isAbandoned"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_9']
        field_isAbandoned_value = resolver(field_shoppingCart_value, info)
        nested_shoppingCart_result["isAbandoned"] = field_isAbandoned_value
        info.field_name = "items"
        info.parent_type = "ShoppingCart"
        resolver = _resolvers['resolver_10']
        field_items_value = resolver(field_shoppingCart_value, info)
        if field_items_value is not None:
            if isinstance(field_items_value, list):
                nested_shoppingCart_result["items"] = []
                for item_items in field_items_value:
                    item_items_result = {}
                    info.field_name = "quantity"
                    info.parent_type = "CartItem"
                    resolver = _resolvers['resolver_11']
                    field_quantity_value = resolver(item_items, info)
                    item_items_result["quantity"] = field_quantity_value
                    info.field_name = "subtotal"
                    info.parent_type = "CartItem"
                    resolver = _resolvers['resolver_12']
                    field_subtotal_value = resolver(item_items, info)
                    item_items_result["subtotal"] = field_subtotal_value
                    info.field_name = "originalPrice"
                    info.parent_type = "CartItem"
                    resolver = _resolvers['resolver_13']
                    field_originalPrice_value = resolver(item_items, info)
                    item_items_result["originalPrice"] = field_originalPrice_value
                    info.field_name = "totalSavings"
                    info.parent_type = "CartItem"
                    resolver = _resolvers['resolver_14']
                    field_totalSavings_value = resolver(item_items, info)
                    item_items_result["totalSavings"] = field_totalSavings_value
                    info.field_name = "product"
                    info.parent_type = "CartItem"
                    resolver = _resolvers['resolver_15']
                    field_product_value = resolver(item_items, info)
                    if field_product_value is not None:
                        nested_product_result = {}
                        info.field_name = "name"
                        info.parent_type = "Product"
                        resolver = _resolvers['resolver_16']
                        field_name_value = resolver(field_product_value, info)
                        nested_product_result["name"] = field_name_value
                        info.field_name = "price"
                        info.parent_type = "Product"
                        resolver = _resolvers['resolver_17']
                        field_price_value = resolver(field_product_value, info)
                        nested_product_result["price"] = field_price_value
                        info.field_name = "finalPrice"
                        info.parent_type = "Product"
                        resolver = _resolvers['resolver_18']
                        field_finalPrice_value = resolver(field_product_value, info)
                        nested_product_result["finalPrice"] = field_finalPrice_value
                        info.field_name = "savings"
                        info.parent_type = "Product"
                        resolver = _resolvers['resolver_19']
                        field_savings_value = resolver(field_product_value, info)
                        nested_product_result["savings"] = field_savings_value
                        info.field_name = "isOnSale"
                        info.parent_type = "Product"
                        resolver = _resolvers['resolver_20']
                        field_isOnSale_value = resolver(field_product_value, info)
                        nested_product_result["isOnSale"] = field_isOnSale_value
                        item_items_result["product"] = nested_product_result
                    else:
                        item_items_result["product"] = None
                    nested_shoppingCart_result["items"].append(item_items_result)
            else:
                single_item_result = {}
                info.field_name = "quantity"
                info.parent_type = "CartItem"
                resolver = _resolvers['resolver_21']
                field_quantity_value = resolver(field_items_value, info)
                single_item_result["quantity"] = field_quantity_value
                info.field_name = "subtotal"
                info.parent_type = "CartItem"
                resolver = _resolvers['resolver_22']
                field_subtotal_value = resolver(field_items_value, info)
                single_item_result["subtotal"] = field_subtotal_value
                info.field_name = "originalPrice"
                info.parent_type = "CartItem"
                resolver = _resolvers['resolver_23']
                field_originalPrice_value = resolver(field_items_value, info)
                single_item_result["originalPrice"] = field_originalPrice_value
                info.field_name = "totalSavings"
                info.parent_type = "CartItem"
                resolver = _resolvers['resolver_24']
                field_totalSavings_value = resolver(field_items_value, info)
                single_item_result["totalSavings"] = field_totalSavings_value
                info.field_name = "product"
                info.parent_type = "CartItem"
                resolver = _resolvers['resolver_25']
                field_product_value = resolver(field_items_value, info)
                if field_product_value is not None:
                    nested_product_result = {}
                    info.field_name = "name"
                    info.parent_type = "Product"
                    resolver = _resolvers['resolver_26']
                    field_name_value = resolver(field_product_value, info)
                    nested_product_result["name"] = field_name_value
                    info.field_name = "price"
                    info.parent_type = "Product"
                    resolver = _resolvers['resolver_27']
                    field_price_value = resolver(field_product_value, info)
                    nested_product_result["price"] = field_price_value
                    info.field_name = "finalPrice"
                    info.parent_type = "Product"
                    resolver = _resolvers['resolver_28']
                    field_finalPrice_value = resolver(field_product_value, info)
                    nested_product_result["finalPrice"] = field_finalPrice_value
                    info.field_name = "savings"
                    info.parent_type = "Product"
                    resolver = _resolvers['resolver_29']
                    field_savings_value = resolver(field_product_value, info)
                    nested_product_result["savings"] = field_savings_value
                    info.field_name = "isOnSale"
                    info.parent_type = "Product"
                    resolver = _resolvers['resolver_30']
                    field_isOnSale_value = resolver(field_product_value, info)
                    nested_product_result["isOnSale"] = field_isOnSale_value
                    single_item_result["product"] = nested_product_result
                else:
                    single_item_result["product"] = None
                nested_shoppingCart_result["items"] = single_item_result
        else:
            nested_shoppingCart_result["items"] = None
        result["shoppingCart"] = nested_shoppingCart_result
    else:
        result["shoppingCart"] = None
    return result


# Initialize resolvers for standalone execution
_resolvers['resolver_0'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_1'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_2'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_3'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_4'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_5'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_6'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_7'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_8'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_9'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_10'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_11'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_12'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_13'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_14'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_15'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_16'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_17'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_18'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_19'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_20'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_21'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_22'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_23'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_24'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_25'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_26'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_27'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_28'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_29'] = _default_resolver  # Custom resolver in actual execution
_resolvers['resolver_30'] = _default_resolver  # Custom resolver in actual execution


if __name__ == '__main__':
    # Example usage when run standalone
    print('This is a JIT-compiled GraphQL executor.')
    print('To use it, import and call execute_query() with your root object.')
    print()
    print('Example:')
    print('  from this_file import execute_query')
    print('  result = execute_query(root_object)')
    print('  print(result)')
    
    # Demo with sample data
    class SampleObject:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    # You can test with your own data structure here
    # sample_root = SampleObject(...)
    # result = execute_query(sample_root)
    # print(result)