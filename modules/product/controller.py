from flask import request, jsonify
import logging
from extensions import db
from modules.product.entity import Product
from modules.product.schema import ProductSchema
from modules.product.middleware import data_validation

from modules.product.services import handle_document_from_s3, update_product_category_service, batch_translate_service, semantic_search_service, batch_embedding_product_service

# Initialize the ProductSchema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def classify_products():
    try:
        product_ids = request.json.get('product_ids', [])
        if not product_ids:
            return jsonify({'error': 'Product IDs are required'}), 400
        
        result = update_product_category_service(product_ids)
        
        return jsonify({
            'message': 'Products classified successfully',
            'classified_products': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error classifying products: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
    
def translate_product_info():
    try:
        batch_translate_service()
        
        return jsonify({
            'message': 'success',
            # 'translated_product_info': translated_product_info
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error translating products ======== \n{str(e)}\n\n")
        return jsonify({'error': str(e)}), 500
    
    
def embed_products():
    try:
        response = batch_embedding_product_service()
        
        return jsonify({
            'message': response
        })
        
    except Exception as e:
        logger.error(f"\n\n======== Error embedding products ======== \n{str(e)}\n\n")
        return jsonify({'error from embed_products': str(e)}), 500
    
    
def semantic_search():
    try:
        query_text = request.args.get('query')
        if not query_text:
            return jsonify({'message': 'query text required'})
        
        response = semantic_search_service(query_text)
        
        
        return jsonify({
            'message': response,
            # 'translated_product_info': translated_product_info
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error searching products ======== \n{str(e)}\n\n")
        return jsonify({'error': str(e)}), 500
    

def extract_text():
    try:
        path = request.json.get('path')
        response = handle_document_from_s3(path)

        return jsonify({
            'message': response,
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error from extract_text controller ======== \n{str(e)}\n\n")
        return jsonify({'error': str(e)}), 500
    
    
    
