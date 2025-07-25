from flask import jsonify, request
import logging
from modules.product.schema import ProductSchema

# Initialize the ProductSchema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def data_validation():

    if not request.is_json:
        logger.error("Request data is not JSON")
        return jsonify({'error': 'Request data must be JSON'}), 400

    data = request.get_json()
    logger.info(f"Received data for new product: {data}")

    errors = product_schema.validate(data)
    if (errors):
        # logger.error(f"Validation errors: {errors}")
        return {'errors': errors}, 400
    
    return data, 200
