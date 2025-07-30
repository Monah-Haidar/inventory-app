import boto3
import logging
from dotenv import load_dotenv

from extensions import get_logger

class TranslateService:
    def __init__(self):
        load_dotenv()
        self.logger = get_logger()
        self.client = boto3.client('translate', region_name='us-east-1')

    def translate_to_arabic(self, text):
        try:
            response = self.client.translate_text(
                Text=text,
                SourceLanguageCode='en',
                TargetLanguageCode='ar'
            )
            return response['TranslatedText']
        except Exception as e:
            self.logger.error(f"\n\n======== Error invoke translation service ========\n{str(e)}\n\n")
            raise
