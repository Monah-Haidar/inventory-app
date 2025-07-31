import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from extensions import get_logger


class BedrockService:
    def __init__(self):
        load_dotenv()
        self.logger = get_logger()
        self.client = boto3.client('bedrock-runtime', region_name='us-east-1')

    def invoke_model_with_request(self, prompt):
        try:
            
            self.logger.info(f"============ Entering Invoke Model ========== \n")
            self.logger.info(f"\n\n====== Invoking model with prompt ======= \n {prompt}\n\n")
            
            model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
            self.logger.info(f"Using model ID: {model_id}")
            
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
            self.logger.info(f"\n\nNative request for model invocation\n\n{native_request}\n\n")
            
            request = json.dumps(native_request)
            self.logger.info(f"\n\nRequest to invoke model\n\n{request}\n\n")
            
            try:
                response = self.client.invoke_model(modelId=model_id, body=request)
            except Exception as e:
                self.logger.error(f"\n\nError invoking model:\n\n{e}\n\n")
                raise
            self.logger.info(f"\n\n====== Response from model ======= \n {model_id}: {response}\n\n")
            
            model_response = json.loads(response["body"].read())
            
            response_text = model_response["content"][0]["text"]
            
            return response_text
        
        except (ClientError, Exception) as e:
            print(f"ERROR: Can't invoke 'anthropic.claude-3-5-sonnet-20240620-v1:0'. Reason: {e}")
            raise


    def get_embedding(self, text):
        body = {
            "inputText": text
        }
        response = self.client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response['body'].read())
        
        return result['embedding']
    
    def extract_text_from_document(self, file_bytes):
        """
        Extract text from document bytes using Anthropic Claude 3.5 Sonnet on Bedrock.
        The document is sent as a base64-encoded string in the prompt.
        Returns the extracted text as a string.
        """
        import base64
        try:
            self.logger.info("[Bedrock] extract_text_from_document called. Sending document bytes to Claude 3.5 Sonnet model.")

            model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
            b64_doc = base64.b64encode(file_bytes).decode('utf-8')
            prompt = (
                "You will receive a document as a base64-encoded file. "
                "Extract all readable text from the document. "
                "Respond ONLY with the extracted text, no explanations.\n\n"
                "Document (base64):\n" + b64_doc
            )
            native_request = {
                "anthropic_version": 'bedrock-2023-05-31',
                "max_tokens": 2048,
                "temperature": 0.0,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}],
                    }
                ],
            }
            request = json.dumps(native_request)
            response = self.client.invoke_model(
                modelId=model_id,
                body=request,
                contentType="application/json",
                accept="application/json"
            )
            self.logger.info(f"[Bedrock] Claude 3.5 Sonnet extraction response received.")
            model_response = json.loads(response["body"].read())
            extracted_text = model_response["content"][0]["text"]
            self.logger.info(f"[Bedrock] Extracted text: {extracted_text[:100]}...")  # Log first 100 chars
            return extracted_text
        except Exception as e:
            self.logger.error(f"[Bedrock] Error extracting text from document: {str(e)}")
            raise