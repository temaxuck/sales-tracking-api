from datetime import date

from marshmallow import Schema, validates, ValidationError, validates_schema
from marshmallow.fields import Str, Int, Float, Date, List, Nested
from marshmallow.validate import Length, OneOf, Range

from sales.config import Config


class ProductSchema(Schema):
    name = Str(validate=Length(min=1, max=256), required=True)
    price = Float(validate=Range(min=0), required=True)


class ProductsSchema(Schema):
    products = Nested(
        ProductSchema,
        many=True,
        required=True,
        validate=Length(max=Config.MAX_PRODUCT_INSTANCES_WITHIN_IMPORT),
    )


class ProductsResponseSchema(Schema):
    products = Nested(
        ProductSchema,
        many=True,
        required=True,
    )


class EmptyResponseSchema(Schema):
    pass
