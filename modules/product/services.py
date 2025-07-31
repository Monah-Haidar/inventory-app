from modules.product.entity import Product

from dotenv import load_dotenv
import json
from extensions import db, get_logger
from modules.product.schema import ProductSchema
from modules.shared.services.bedrock import BedrockService
from modules.shared.services.translate import TranslateService
from modules.shared.services.s3 import S3Service

# from modules.shared.services.bedrock.service import bedrock_service

   

class ProductService:
    def __init__(self):
        load_dotenv()
        self.product_schema = ProductSchema()
        self.products_schema = ProductSchema(many=True)
        self.logger = get_logger()
        self.bedrock_service = BedrockService()
        self.translate_service = TranslateService()
        self.s3_service = S3Service()

    def update_product_category(self, product_ids):
        try:
            products_list = []
            for product_id in product_ids:
                product = Product.query.get(product_id)
                if not product:
                    continue
                products_list.append({'id': product.id, 'name': product.name})

            product_lines = []
            for idx, product in enumerate(products_list, start=1):
                product_lines.append(f'{idx}. id: {product["id"]}, name: "{product["name"]}"')

            products_text = "\n".join(product_lines)
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

            self.logger.info(f"\n=============== Invoking AI model ===============\n")
            classified_category = self.bedrock_service.invoke_model_with_request(prompt)
            self.logger.info(f"\n=============== Classified category for product ===============\n {classified_category}")
            return json.loads(classified_category)
        except Exception as e:
            self.logger.error(f"Error updating product category: {str(e)}")
            raise

    def batch_translate(self):
        try:
            products_to_translate = Product.query.filter((Product.name_ar == None) | (Product.description_ar == None)).all()
            for product in products_to_translate:
                product.name_ar = self.translate_service.translate_to_arabic(product.name)
                product.description_ar = self.translate_service.translate_to_arabic(product.description)
                db.session.commit()
            self.logger.info(f"===== Batch Translation Complete =====")
        except Exception as e:
            self.logger.error(f"\n\n======== Error batch translating text ========\n{str(e)}\n\n")
            raise

    def embed_product(self, product):
        text = f"{product.name} {product.description or ''} {product.category} {product.price} {product.name_ar or ''} {product.description_ar or ''}"
        vector = self.bedrock_service.get_embedding(text)
        self.logger.info(f"\n\n===== Embedded Vector =====\n\n{vector}")
        product.embedding = vector
        db.session.commit()

    def batch_embedding(self):
        try:
            products_to_embed = Product.query.filter(Product.embedding == None).all()
            self.logger.info(f"\n\n===== Products to embed =====\n\n{[(p.id, p.name) for p in products_to_embed]}")
            for product in products_to_embed:
                self.embed_product(product)
            return "Batch Embedding Complete"
        except Exception as e:
            self.logger.error(f"\n\n======== Error with batch embedding ========\n{str(e)}\n\n")
            raise

    def semantic_search(self, query_text):
        try:
            query_vector = self.bedrock_service.get_embedding(query_text)
            self.logger.info(f"\n\n===== Search Vector =====\n\n{query_vector[:100]}")
            
            query = Product.query.filter((Product.embedding.isnot(None)) & (Product.in_stock == True))
            self.logger.info(f"\n\n===== ORM Query =====\n\n{query}")
            
            results = query.order_by(Product.embedding.cosine_distance(query_vector)).limit(30).all()
            self.logger.info(f"\n\n===== Cosine query result =====\n\n{results}")
            
            search_results = []
            for product in results:
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
                    'similarity_score': 1 - float(distance)
                })
                
            self.logger.info(f"\n\n===== Search Results =====\n\n{search_results}")
            return search_results
        
        except Exception as e:
            self.logger.error(f"\n\n======== Error with similarity search ========\n{str(e)}\n\n")
            raise

    def handle_document_from_s3(self, s3_path):
        try:
            if s3_path.startswith('s3://'):
                s3_path = s3_path[5:]
            parts = s3_path.split('/', 1)
            if len(parts) != 2:
                self.logger.error(f"Invalid S3 path: {s3_path}")
                raise ValueError("Invalid S3 path. Must be in format 'bucket/key/to/file'.")
            
            bucket_name, object_key = parts
            
            self.logger.info(f"[DocumentProcessing] Downloading from S3: bucket={bucket_name}, key={object_key}")
            file_bytes = self.s3_service.read_file_from_s3(bucket_name, object_key)

            self.logger.info(f"[DocumentProcessing] Extracting text with Bedrock model...")
            extracted_text = self.bedrock_service.extract_text_from_document(file_bytes)

            self.logger.info(f"[DocumentProcessing] Extraction complete. Text length: {len(extracted_text) if extracted_text else 0}")
            return extracted_text
        
        except Exception as e:
            self.logger.error(f"[DocumentProcessing] Error processing document from S3: {str(e)}")
            raise


