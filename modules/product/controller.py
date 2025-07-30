from flask import request, jsonify
import logging
from modules.product.services import ProductService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

product_service = ProductService()


def classify_products():
    try:
        product_ids = request.json.get('product_ids', [])
        if not product_ids:
            return jsonify({'message': 'Product IDs are required'}), 400

        result = product_service.update_product_category(product_ids)

        return jsonify({
            'success': True,
            'message': 'Products classified successfully',
            'data': {'classified_products': result}
        }), 200
        
    except Exception as e:
        logger.error(f"Error classifying products: {str(e)}")
        return jsonify({'success': False, 'message': 'An internal error occurred. Please try again later.'}), 500
    
    
    
def translate_product_info():
    try:
        product_service.batch_translate()
        
        return jsonify({
            'success': True,
            'message': 'Translation completed successfully',
            'data': None
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error translating products ======== \n{str(e)}\n\n")
        return jsonify({'success': False, 'message': 'An internal error occurred. Please try again later.'}), 500
    
    
def embed_products():
    try:
        response = product_service.batch_embedding()
        
        return jsonify({
            'success': True,
            'message': 'Embedding completed successfully',
            'data': {'result': response}
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error embedding products ======== \n{str(e)}\n\n")
        return jsonify({'success': False, 'message': 'An internal error occurred. Please try again later.'}), 500
    
    
def semantic_search():
    try:
        query_text = request.args.get('query')
        if not query_text:
            return jsonify({'message': 'query text required'})

        response = product_service.semantic_search(query_text)

        return jsonify({
            'success': True,
            'message': 'Semantic search completed successfully',
            'data': response
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error searching products ======== \n{str(e)}\n\n")
        return jsonify({'success': False, 'message': 'An internal error occurred. Please try again later.'}), 500
    

def extract_text():
    try:
        path = request.json.get('path')
        response = product_service.handle_document_from_s3(path)

        return jsonify({
            'success': True,
            'message': 'Document processed successfully',
            'data': response
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error from extract_text controller ======== \n{str(e)}\n\n")
        return jsonify({'success': False, 'message': 'An internal error occurred. Please try again later.'}), 500
    
    
    
