import logging
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()

def get_logger(level=logging.INFO):
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():
        logging.basicConfig(level=level)
    logger.setLevel(level)
    return logger