from flask import request, jsonify
import logging
from extensions import db
from modules.product.entity import Product
from modules.product.schema import ProductSchema
from modules.product.middleware import data_validation

from modules.product.services import query_products_price_quantity_service, average_product_price_service, get_max_and_min_price_service, get_total_number_of_products_per_category_service, get_out_of_stock_items_service, get_top_5_expensive_items_service, get_items_within_price_range_service, get_products_added_in_the_last_n_days_service, update_product_category_service, batch_translate_service, similarity_search_service, batch_embedding_product_service

# Initialize the ProductSchema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def get_products():
    try:
        products = Product.query.all()
        
        return jsonify({
            'message': 'Data retrieved Successfully', 
            'products': [{
                'id': product.id,
                'name': product.name,   
                'category': product.category,
                'price': product.price,
                'quantity': product.quantity,
                'in_stock': product.in_stock
            } for product in products]}), 200

    except Exception as e:
        return jsonify({'error': str(e)}, 500)
    

def get_product(product_id):
    try:            
        product = Product.query.get(product_id)
        
        if not product:
            logger.warning(f"Product with ID {product_id} not found.")
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'message': 'Product retrieved successfully',
            'product': product_schema.dump(product)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching product with ID {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


def add_product():
    try:       
        data, status_code = data_validation();
        
        if status_code != 200:
            return jsonify(data), status_code

        existing_product = Product.query.filter_by(name=data.get('name')).first()
        logger.info("Data received:", data, type(data))

        if existing_product:
            logger.info(f"Product with name {data.get('name')} already exists.")
            return jsonify({
                'message': 'Product already exists', 
                'product': product_schema.dump(existing_product)
                }), 400

        
        product = Product(**data)
        db.session.add(product)
        db.session.commit()

        return jsonify({
            'message': 'Product added successfully',
            'product': product_schema.dump(product)
        }), 200

    except Exception as e:
        logger.error(f"Error adding product: {str(e)}")
        return jsonify({'error': str(e)}, 500)


def update_product(product_id):
    try:
        data = data_validation();
        
        existing_product = Product.query.get(product_id)
        if not existing_product:
            logger.warning(f"Product with ID {product_id} not found.")
            return jsonify({'error': 'Product not found'}), 404
        
        # Update the product with the new data
        allowed_fields = {'name', 'category', 'price', 'quantity', 'in_stock'}
        for key, value in data.items():
            if key in allowed_fields:
                setattr(existing_product, key, value)
            
        db.session.commit()

        return jsonify({
            'message': 'Product updated successfully',
            'product': product_schema.dump(existing_product)
        }), 200

    except Exception as e:
        logger.error(f"Error adding product: {str(e)}")
        return jsonify({'error': str(e)}, 500)


def delete_product(product_id):
    try:            
        product = Product.query.get(product_id)
        
        if not product:
            logger.warning(f"Product with ID {product_id} not found.")
            return jsonify({'error': 'Product not found'}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product deleted successfully',
            'product': product_schema.dump(product)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching product with ID {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_total_inventory_value():
    try:
        price_quantity = query_products_price_quantity_service();
        total_value = sum(price * quantity for price, quantity in price_quantity)
        
        return jsonify({
            'message': 'success',
            'Total Inventory Value': total_value
        })
    except Exception as e:
        logger.error(f"Error calculating total inventory value: {str(e)}")
        return jsonify({'error': str(e)}), 500
        

def get_average_product_price():
    try:
        average_price = average_product_price_service()
        
        return jsonify({
            'message': 'success',
            'Average product price': average_price
        })
    except Exception as e:
        logger.error(f"Error Average product price: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_maximum_and_minimum_price():
    try:
        max_price, min_price = get_max_and_min_price_service()
       
        return jsonify({
            'message': 'success',
            'Maximum Price': max_price,
            'Minimum Price': min_price
        })
    except Exception as e:
        logger.error(f"Error calculating maximum and minimum price: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_total_number_of_products_per_category():
    try:
        total_value = get_total_number_of_products_per_category_service()
        logger.info(f"Total number of products per category: {total_value}")
        return jsonify({
            'message': 'success',
            'Total number of products per category': total_value
        })
    except Exception as e:
        logger.error(f"Error calculating number of products per category: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_out_of_stock_items():
    try:
        out_of_stock_items = get_out_of_stock_items_service()
        
        return jsonify({
            'message': 'success',
            'Out of stock items list': out_of_stock_items
        })
    except Exception as e:
        logger.error(f"Error retieving items: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_top_5_most_expensive_items():
    try:
        expensive_items = get_top_5_expensive_items_service()
        
        return jsonify({
            'message': 'Top 5 most expensive items retrieved successfully',
            'top 5 most expensive items': expensive_items
        })
    except Exception as e:
        logger.error(f"Error retrieving items: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_items_within_a_price_range():
    try:
        min_price = request.args.get('min', type=float)
        max_price = request.args.get('max', type=float)
        
        if min_price is None or max_price is None:
            return jsonify({'error': 'Both min and max price parameters are required'}), 400
        
        if min_price > max_price:
            return jsonify({'error': 'Min price cannot be greater than max price'}), 400
        
        
        items = get_items_within_price_range_service(min_price,max_price)
        
        return jsonify({
            'message': 'Items retrieved successfully',
            'Items': items
        })
    except Exception as e:
        logger.error(f"Error retrieving items: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_products_added_in_the_last_n_days():
    try:
        nb_of_days = request.args.get('nb', type=int)
        items = get_products_added_in_the_last_n_days_service(nb_of_days)
        
        return jsonify({
            'message': f"Products retrieved successfully",
            f"Products added in the last {nb_of_days} days": items
        })
    except Exception as e:
        logger.error(f"Error retrieving products: {str(e)}")
        return jsonify({'error': str(e)}), 500


def search_by_category():
    try:
        category = request.args.get('category', type=str)
        
        if not category:
            return jsonify({'error': 'Category parameter is required'}), 400
        
        products = Product.query.filter(Product.category.ilike(f'%{category}%')).all()
        
        if not products:
            return jsonify({'message': 'No products found in this category'}), 404
        
        return jsonify({
            'message': 'success',
            'products': products_schema.dump(products)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching products by category: {str(e)}")
        return jsonify({'error': str(e)}), 500


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
        
        similarity_search_service()
        
        
        return jsonify({
            'message': 'success',
            # 'translated_product_info': translated_product_info
        }), 200
        
    except Exception as e:
        logger.error(f"\n\n======== Error searching products ======== \n{str(e)}\n\n")
        return jsonify({'error': str(e)}), 500