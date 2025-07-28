from modules.product.controller import (
    classify_products,
    translate_product_info,
    semantic_search,
    embed_products,
    extract_text
)

def register_product_routes(app):
    app.add_url_rule('/api/products/classify', view_func=classify_products, methods=['POST'])
    app.add_url_rule('/api/products/translate', view_func=translate_product_info, methods=['POST'])
    app.add_url_rule('/api/products/batch-embed', view_func=embed_products, methods=['POST'])
    app.add_url_rule('/api/products/search', view_func=semantic_search, methods=['GET'])
    app.add_url_rule('/api/extract-text', view_func=extract_text, methods=['POST'])