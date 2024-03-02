from datetime import date as datetime_date

from marshmallow import Schema, validates, ValidationError
from marshmallow.fields import Str, Int, Float, Date, Nested, Number, Dict
from marshmallow.validate import Length, Range

from sales.config import Config


class EmptyResponseSchema(Schema):
    pass


class PostProductSchema(Schema):
    name = Str(validate=Length(min=1, max=256), required=True)
    price = Float(validate=Range(min=0), required=True)


class ProductSchema(PostProductSchema):
    product_id = Int(validate=Range(min=0), required=True)


class ProductsSchema(Schema):
    products = Nested(
        PostProductSchema,
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


class SaleItemsSchema(Schema):
    product_id = Int(validate=Range(min=0), required=True)
    quantity = Number(validate=Range(min=0, min_inclusive=False), requred=True)


class BaseSaleSchema(Schema):
    date = Date(format=Config.DATE_FORMAT, required=True)
    items = Nested(SaleItemsSchema, many=True, required=True)

    @validates("date")
    def validate_birth_date(self, value: datetime_date):
        if value > datetime_date.today():
            raise ValidationError("Birth date can't be in the future")

    # Not sure if I should validate it like this
    # @validates_schema
    # def validate_unique_products(self, data, **_):
    #     products_ids = set()
    #     for item in data.get("items"):
    #         if item.get("product_id") in products_ids:
    #             raise ValidationError(
    #                 f"product_id {item.get("product_id")} is not unique. Please provide unique product per item."
    #             )

    #         products_ids.add(item.get("product_id"))


class SaleSchema(BaseSaleSchema):
    sale_id = Int(validate=Range(min=0), required=True)
    amount = Float(validate=Range(min=0), required=True)


class GetSalesResponseSchema(Schema):
    sales = Nested(SaleSchema, many=True, required=True)


class MetricsSchema(Schema):
    total_sales = Float(validate=Range(min=0), required=True, allow_none=True)
    average_sales = Float(validate=Range(min=0), required=True, allow_none=True)
    sales_trends = Dict(keys=Str(), values=Float(validate=Range(min=0)), required=True)
