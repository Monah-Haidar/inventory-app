from pgvector.sqlalchemy import Vector
from extensions import db
from datetime import datetime
# from pgvector.sqlalchemy.vector import Vector

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    name_ar = db.Column(db.String(100), nullable=True)
    description_ar = db.Column(db.String(255), nullable=True)
    # category = db.Column(db.Enum('Electronics', 'Clothing', 'Food'), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    in_stock = db.Column (db.Boolean, default=True)
    embedding = db.Column(Vector(1024), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

