import boto3
import logging
from dotenv import load_dotenv
from botocore.exceptions import ClientError

from extensions import get_logger



class S3Service:
    def __init__(self):
        load_dotenv()
        self.logger = get_logger()
        self.client = boto3.client('s3', region_name='us-east-1')

    def read_file_from_s3(self, bucket_name, object_key):
        
        self.logger.info(f"[S3] Reading file: bucket='{bucket_name}', key='{object_key}'")
        
        try:
            self.check_bucket_exists(bucket_name)
            
            response = self.get_object_from_s3(bucket_name, object_key)
            
            file_bytes = response['Body'].read()
            self.logger.info(f"[S3] Read {len(file_bytes)} bytes from '{object_key}' in '{bucket_name}'")
            
            return file_bytes
        
        except ValueError as e:
            self.logger.error(f"[S3] Access Error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"[S3] Unexpected Error: {str(e)}")
            raise

    def check_bucket_exists(self, bucket_name):
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ('404', '403'):
                self.logger.error(f"[S3] Bucket '{bucket_name}' does not exist or access denied.")
                raise ValueError(f"Bucket '{bucket_name}' does not exist or you don't have access to it")
            raise

    def get_object_from_s3(self, bucket_name, object_key):
        try:
            return self.client.get_object(Bucket=bucket_name, Key=object_key)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.error(f"[S3] Object '{object_key}' does not exist in bucket '{bucket_name}'")
                raise ValueError(f"Object '{object_key}' does not exist in bucket '{bucket_name}'")
            raise
