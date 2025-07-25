
from marshmallow import fields, validate
from extensions import ma
from modules.product.entity import Product
from typing import List, Optional


class ProductSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Product
        load_instance = True
    
    id = ma.auto_field(dump_only=True)
    name = ma.auto_field(required=True)
    description = ma.auto_field(required=True)
    name_ar = ma.auto_field(required=False)
    description_ar = ma.auto_field(required=False)
    category = ma.auto_field(required=False)
    price = ma.auto_field(required=True)
    quantity = ma.auto_field(required=True)
    in_stock = ma.auto_field(required=True)
    # embedding = fields.List(fields.Float(), allow_none=True)
    # embedding = ma.auto_field(required=False)
    created_at = ma.auto_field()
    embedding = fields.List(fields.Float(), allow_none=True, load_only=True)