from flask import jsonify
from sqlalchemy import func
from modules.product.entity import Product
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import boto3
import json
import io
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





def invoke_model_with_request(prompt):
    try:
        logger.info(f"============ Entering Invoke Modle ========== \n")
        try:
            client = boto3.client('bedrock-runtime', region_name='us-east-1')
        except Exception as e:
            logger.error(f"Error creating Bedrock client: {e}")
            raise
        
        logger.info(f"\n\n====== Invoking model with prompt ======= \n {prompt}\n\n")
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
        logger.info(f"\n\nNative request for model invocation\n\n{native_request}\n\n")
        
        request = json.dumps(native_request)
        logger.info(f"\n\nRequest to invoke model\n\n{request}\n\n")
        
        try:
            response = client.invoke_model(modelId=model_id, body=request)
        except Exception as e:
            logger.error(f"\n\nError invoking model:\n\n{e}\n\n")
            raise
        logger.info(f"\n\n====== Response from model ======= \n {model_id}: {response}\n\n")
        
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
    
    
    
# from urllib.parse import urlparse, unquote

# def parse_s3_url(s3_url):
#     """
#     Parse an S3 URL into bucket and key.
#     Supports virtual-hosted-style URLs including regional endpoints.
#     """
#     parsed = urlparse(s3_url)
    
#     if not parsed.netloc.endswith('amazonaws.com'):
#         raise ValueError("Invalid S3 URL format")
    
#     # URL decode the path to handle spaces and special characters
#     decoded_path = unquote(parsed.path)
#     host_parts = parsed.netloc.split('.')
    
#     # Handle regional endpoints: bucket-name.s3.region.amazonaws.com
#     if len(host_parts) > 4 and host_parts[1] == 's3':
#         bucket = host_parts[0]
#         key = parsed.path.lstrip('/')
#         return bucket, unquote(key)
#     # Handle path-style URLs: s3.amazonaws.com/bucket-name/key
#     elif host_parts[0] == 's3':
#         parts = parsed.path.lstrip('/').split('/', 1)
#         if len(parts) != 2:
#             raise ValueError("Invalid S3 path format")
#         bucket = parts[0]
#         key = parts[1]
#         return bucket, unquote(key)
#     # Handle legacy style: bucket-name.s3.amazonaws.com/key
#     else:
#         bucket = host_parts[0]
#         key = parsed.path.lstrip('/')
#         return bucket, unquote(key)

    


s3 = boto3.client('s3', region_name='us-east-1')

def read_file_from_s3(s3_path):
    try:
        # https://zeroandone-inventory-app-bucket.s3.us-east-1.amazonaws.com/Chapter+1+(Databases+and+Database+Users).pdf
        # https://zeroandone-inventory-app-bucket.s3.us-east-1.amazonaws.com/Mini_Inventory_Management_System.docx
        # https://zeroandone-inventory-app-bucket.s3.us-east-1.amazonaws.com/5-+Multi-containers+apps.pdf
        # https://zeroandone-inventory-app-bucket.s3.us-east-1.amazonaws.com/Module+6+-+Storage.md
        bucket_name = 'zeroandone-inventory-app-bucket'
        object_key = 'Screenshot 2025-07-28 234043.png'
        # bucket_name, object_key = parse_s3_url(s3_path)
        logger.info(f"\n\n======== Bucket, Key 1 ======== \n{bucket_name, object_key}\n\n")
        
        # Check if bucket exists first
        try:
            s3.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404' or error_code == '403':
                logger.error(f"\n\n======== Bucket {bucket_name} does not exist or you don't have access to it ========\n\n")
                raise ValueError(f"Bucket '{bucket_name}' does not exist or you don't have access to it")
            raise

        # Try to get the object
        try:
            response = s3.get_object(Bucket=bucket_name, Key=object_key)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"\n\n======== Object {object_key} does not exist in bucket {bucket_name} ========\n\n")
                raise ValueError(f"Object '{object_key}' does not exist in bucket '{bucket_name}'")
            raise

        file_bytes = response['Body'].read()
        logger.info(f"\n\n======== file_bytes ======== \n{file_bytes[:500]}\n\n")
        
        return file_bytes
        
    except ValueError as e:
        logger.error(f"\n\n======== S3 Access Error ========\n{str(e)}\n\n")
        raise
    except Exception as e:
        logger.error(f"\n\n======== Unexpected Error ========\n{str(e)}\n\n")
        raise



textract = boto3.client('textract')

def extract_text_with_textract(file_bytes):
    
    try:
        # response = textract.analyze_document(
        #     Document={'Bytes': file_bytes},
        #     FeatureTypes=['FORMS', 'TABLES']
        # )
        response = textract.detect_document_text(
            Document={'Bytes': file_bytes},
            # FeatureTypes=['FORMS', 'TABLES', '']
        )
    except Exception as e:
        logger.error(f"\n\n======== extract_text_with_textract service Error ========\n{str(e)}\n\n")
        raise
    
    
    text_chunks = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            text_chunks.append(block['Text'])
            
    logger.info(f"\n\n======== text_chunks ======== \n{text_chunks}\n\n")

    full_text = "\n".join(text_chunks)
    logger.info(f"\n\n======== full_text ======== \n{full_text}\n\n")

    return full_text



# bedrock = boto3.client('bedrock-runtime')

def structure_with_bedrock(text):
    prompt = f"""
    Given the following document text, extract structured data into a JSON format:

    -----
    {text}
    -----

    Return a well-formatted JSON.
    """

    response = invoke_model_with_request(prompt)
    logger.info(f"\n=============== GOT PAST RESPONSE ===============\n")
    result = response['body']
    logger.info(f"\n=============== RESULT ===============\n {result}")
    return result




def handle_document_from_s3(s3_path):
    file_name = s3_path.split('/')[-1]
    file_bytes = read_file_from_s3(s3_path)
    
    text = extract_text_with_textract(file_bytes)
    structured_output = structure_with_bedrock(text)
    
    return structured_output
    # return process_with_bedrock(file_bytes, file_name)
