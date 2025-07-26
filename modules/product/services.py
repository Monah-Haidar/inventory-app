from sqlalchemy import func
from modules.product.entity import Product
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import boto3
import json
import os
import logging
from extensions import db
import numpy as np
from modules.product.schema import ProductSchema

load_dotenv()

# Initialize the ProductSchema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def query_products_price_quantity_service():
    return Product.query.with_entities(Product.price, Product.quantity).all()

def average_product_price_service():
    price_quantity = query_products_price_quantity_service()
    total_value = sum(price * quantity for price, quantity in price_quantity)
    total_products = sum(quantity for _, quantity in price_quantity)
    
    if total_products == 0:
        return 0
    
    average_price = total_value / total_products
    
    return round(average_price, 2)


def get_max_and_min_price_service():
    price= Product.query.with_entities(Product.price).all()
    
    if not price:
        return None, None
    
    max_price = max(price for price, in price);
    min_price = min(price for price, in price);
    
    return max_price, min_price


def get_total_number_of_products_per_category_service():
    categories = Product.query.with_entities(Product.category, func.count(Product.id)).group_by(Product.category).all()
    
    total_value = {category: count for category, count in categories}

    return total_value


def get_out_of_stock_items_service():
    out_of_stock_items = Product.query.filter(Product.in_stock == 0).all()
    
    if not out_of_stock_items:
        return 0
    
    out_of_stock_data = [{'id': item.id, 'name': item.name, 'category': item.category} for item in out_of_stock_items]
    
    return out_of_stock_data


def get_top_5_expensive_items_service():
    top_items = Product.query.order_by(Product.price.desc()).limit(5).all()
    
    if not top_items:
        return []
    
    top_items_data = [{'id': item.id, 'name': item.name, 'price': item.price} for item in top_items]
    
    return top_items_data


def get_items_within_price_range_service(min_price, max_price):
    items = Product.query.filter(Product.price.between(min_price, max_price)).all()
    
    if not items:
        return []
    
    items_data = [{'id': item.id, 'name': item.name, 'price': item.price} for item in items]
    
    return items_data


def get_products_added_in_the_last_n_days_service(nb):
    cutoff = datetime.utcnow() - timedelta(days=nb)

    items = Product.query.filter(Product.created_at >= cutoff).all()

    if not items:
        return []
    
    return [{'id': item.id, 'name': item.name, 'category': item.category, 'created_at': item.created_at} for item in items]


def invoke_model_with_request(prompt):
    try:
        logger.info(f"============ Entering Invoke Modle ========== \n")
        try:
            client = boto3.client('bedrock-runtime', region_name='us-east-1')
        except Exception as e:
            logger.error(f"Error creating Bedrock client: {e}")
            raise
        
        logger.info(f"====== Invoking model with prompt ======= \n {prompt}")
        # v3.5 Sonnet model
        model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        logger.info(f"Using model ID: {model_id}")
        # # v3.7 Sonnet model
        # model_id = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
        
        native_request = {
            "anthropic_version": 'bedrock-2023-05-31',
            "max_tokens": 512,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }
        logger.info(f"Native request for model invocation: {native_request}")
        
        request = json.dumps(native_request)
        logger.info(f"Request to invoke model: {request}")
        
        try:
            response = client.invoke_model(modelId=model_id, body=request)
        except Exception as e:
            logger.error(f"Error invoking model: {e}")
            raise
        logger.info(f"====== Response from model ======= \n {model_id}: {response}")
        
        model_response = json.loads(response["body"].read())

        response_text = model_response["content"][0]["text"]
        
        return response_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        raise

   
def update_product_category_service(product_ids):
    try:
        products_list = []
        # logger.info(f"\n=============== Product IDs for classification ===============:\n {product_ids}")
        for product_id in product_ids:
            product = Product.query.get(product_id)
            if not product:
                continue
            
            products_list.append({'id': product.id, 'name': product.name})
            
        # logger.info(f"for loop ends")
    
        # logger.info(f"\n=============== Products list for classification ===============:\n {products_list}")
        
        product_lines = []
        for idx, product in enumerate(products_list, start=1):
            product_lines.append(f'{idx}. id: {product["id"]}, name: "{product["name"]}"')

        products_text = "\n".join(product_lines)

        # logger.info(f"\n=============== Products text for AI classification ===============\n{products_text}")
        prompt = (
            "You are a product classifier AI.\n"
            "Given a product ID and name, classify each product into a relevant category.\n"
            "Respond ONLY in the following JSON format:\n\n"
            "[\n"
            "  {\n"
            "    \"id\": 1,\n"
            "    \"name\": \"iPhone 14 Pro\",\n"
            "    \"category\": \"Smartphones\"\n"
            "  }\n"
            "]\n\n"
            "Do not include explanations or extra text.\n\n"
            f"Here are the products to classify:\n{products_text}"
        )

        # logger.info(f"\n=============== Prompt for AI classification ===============\n{prompt}")
        
        logger.info(f"\n=============== Invoking AI model ===============\n")
        classified_category = invoke_model_with_request(prompt)
        logger.info(f"\n=============== Classified category for product ===============\n {classified_category}")
        
        return json.loads(classified_category)
        
        
    except Exception as e:
        logger.error(f"Error updating product category: {str(e)}")
        raise
        
        
def translate_to_arabic_service(text):
    try: 
        translate = boto3.client('translate', region_name='us-east-1')

        response = translate.translate_text(
            Text=text,
            SourceLanguageCode='en',
            TargetLanguageCode='ar'
        )
        
        return response['TranslatedText']
        
    except Exception as e:
        logger.error(f"\n\n======== Error invoke translation service ========\n{str(e)}\n\n")
        raise
    
    
def batch_translate_service():
    try:
        products_to_translate = Product.query.filter((Product.name_ar == None) | (Product.description_ar == None)).all()
        for product in products_to_translate:
            product.name_ar = translate_to_arabic_service(product.name)
            product.description_ar = translate_to_arabic_service(product.description)
            db.session.commit()
            
        logger.info(f"===== Batch Translation Complete =====")
        
    except Exception as e:
        logger.error(f"\n\n======== Error batch translating text ========\n{str(e)}\n\n")
        raise


def get_embedding(text):
    bedrock = boto3.client("bedrock-runtime")
    
    body = {
        "inputText": text
    }
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )
    result = json.loads(response['body'].read())
    # logger.info(f"\n\n===== Embedding Response =====\n\n{result}")
    return result['embedding']


def embed_product(product):
    text = f"{product.name} {product.description or ''} {product.category} {product.price} {product.name_ar or ''} {product.description_ar or ''}"
    vector = get_embedding(text)
    logger.info(f"\n\n===== Embedded Vector =====\n\n{vector}")
    product.embedding = vector
    db.session.commit()


def batch_embedding_product_service():
    try:
        products_to_embed = Product.query.filter(Product.embedding == None).all()
        logger.info(f"\n\n===== Products to embed =====\n\n{[(p.id, p.name) for p in products_to_embed]}")
        for product in products_to_embed:
            embed_product(product)
            
        return "Batch Embedding Complete"
        
    except Exception as e:
        logger.error(f"\n\n======== Error with batch embedding ========\n{str(e)}\n\n")
        raise

# def cosine_distance(vector1, vector2):
#     """
#     Calculate cosine distance between two vectors
#     Cosine distance = 1 - cosine similarity
#     Range: 0 (identical) to 2 (opposite)
#     """
#     # Convert to numpy arrays
#     v1 = np.array(vector1)
#     v2 = np.array(vector2)
    
#     # Calculate dot product
#     dot_product = np.dot(v1, v2)
    
#     # Calculate magnitudes
#     magnitude1 = np.linalg.norm(v1)
#     magnitude2 = np.linalg.norm(v2)
    
#     # Calculate cosine similarity
#     cosine_similarity = dot_product / (magnitude1 * magnitude2)
    
#     # Convert to cosine distance
#     cosine_distance = 1 - cosine_similarity
    
#     return cosine_distance
    
def semantic_search_service(query_text):
    try:
        query_vector = get_embedding(query_text)
        logger.info(f"\n\n===== Search Vector =====\n\n{query_vector[:100]}")
        
        query = Product.query.filter((Product.embedding.isnot(None)) & (Product.in_stock == True))
        logger.info(f"\n\n===== ORM Query =====\n\n{query}")
        
        # Implement cosine similarity using pgvector
        results = query.order_by(Product.embedding.cosine_distance(query_vector)).limit(30).all()
        logger.info(f"\n\n===== Cosine query result =====\n\n{results}")
        
        # Format results with similarity scores
        search_results = []
        for product in results:
            # Calculate the actual distance for this product
            distance = db.session.query(Product.embedding.cosine_distance(query_vector)).filter(
                Product.id == product.id
            ).scalar()
            
            search_results.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'category': product.category,
                'price': product.price,
                'distance': float(distance),
                'similarity_score': 1 - float(distance)  # Convert distance to similarity
            })
        
        logger.info(f"\n\n===== Search Results =====\n\n{search_results}")
        return search_results
        
    
    except Exception as e:
        logger.error(f"\n\n======== Error with similartiy search ========\n{str(e)}\n\n")
        raise
    
    