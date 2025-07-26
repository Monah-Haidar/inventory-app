from modules.product.controller import (
    get_products,
    get_product,
    add_product,
    update_product,
    delete_product,
    get_total_inventory_value,
    get_average_product_price,
    get_maximum_and_minimum_price,
    get_total_number_of_products_per_category,
    get_out_of_stock_items,
    get_top_5_most_expensive_items,
    get_items_within_a_price_range,
    get_products_added_in_the_last_n_days,
    search_by_category,
    classify_products,
    translate_product_info,
    semantic_search,
    embed_products
)

def register_product_routes(app):
    app.add_url_rule('/api/products', view_func=get_products, methods=['GET'])
    app.add_url_rule('/api/products/<int:product_id>', view_func=get_product, methods=['GET'])
    app.add_url_rule('/api/products', view_func=add_product, methods=['POST'])
    app.add_url_rule('/api/products/<int:product_id>', view_func=update_product, methods=['PUT'])
    app.add_url_rule('/api/products/<int:product_id>', view_func=delete_product, methods=['DELETE'])

    # Extended APIs
    app.add_url_rule('/api/products/inventory-value', view_func=get_total_inventory_value, methods=['GET'])
    app.add_url_rule('/api/products/average-product-price', view_func=get_average_product_price, methods=['GET'])
    app.add_url_rule('/api/products/max-min-price', view_func=get_maximum_and_minimum_price, methods=['GET'])
    app.add_url_rule('/api/products/number-of-products-per-category', view_func=get_total_number_of_products_per_category, methods=['GET'])
    app.add_url_rule('/api/products/out-of-stock-items', view_func=get_out_of_stock_items, methods=['GET'])
    app.add_url_rule('/api/products/top-5-expensive-items', view_func=get_top_5_most_expensive_items, methods=['GET'])
    app.add_url_rule('/api/products/items-within-price-range', view_func=get_items_within_a_price_range, methods=['GET'])
    app.add_url_rule('/api/products/added-in-last-n-days', view_func=get_products_added_in_the_last_n_days, methods=['GET'])
    app.add_url_rule('/api/products/search-by-category', view_func=search_by_category, methods=['GET'])
    
    # AI APIs
    app.add_url_rule('/api/products/classify', view_func=classify_products, methods=['POST'])
    app.add_url_rule('/api/products/translate', view_func=translate_product_info, methods=['POST'])
    app.add_url_rule('/api/products/batch-embed', view_func=embed_products, methods=['POST'])
    app.add_url_rule('/api/products/search', view_func=semantic_search, methods=['GET'])