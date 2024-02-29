from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from aiomisc import chunk_list
from http import HTTPStatus
from typing import Generator
from sqlalchemy import insert

from sales.api.schema import (
    ProductsSchema,
    EmptyResponseSchema,
    ProductsResponseSchema,
)
from sales.db.schema import product_table
from sales.utils.pg import MAX_QUERY_ARGS, SelectQuery

from .base import BaseView


class ProductsView(BaseView):
    URL_PATH = r"/products"

    MAX_PRODUCTS_PER_INSERT = MAX_QUERY_ARGS // len(product_table.columns)

    @classmethod
    def make_product_table_rows(cls, products: dict) -> Generator:
        """
        Generate rows to insert into `product_table` lazily.
        """

        for product in products:
            yield {
                "name": product["name"],
                "price": product["price"],
            }

    @docs(summary="Get a list of all products")
    @response_schema(ProductsResponseSchema(), code=HTTPStatus.OK.value)
    async def get(self):
        query = product_table.select()

        async with self.pg.acquire() as conn:
            data = [self.serialize_row(row) async for row in SelectQuery(query, conn)]

        return web.json_response(data={"products": data})

    @docs(summary="Add a list of products")
    @request_schema(ProductsSchema())
    @response_schema(EmptyResponseSchema(), code=HTTPStatus.CREATED.value)
    async def post(self):
        data = await self.request.json()
        async with self.pg.acquire() as conn:
            async with conn.begin() as _:
                products = data.get("products")
                products_rows = self.make_product_table_rows(products)

                chunked_products_rows = chunk_list(
                    products_rows, self.MAX_PRODUCTS_PER_INSERT
                )

                for chunk in chunked_products_rows:
                    await conn.execute(insert(product_table).values(chunk))

        return web.Response(status=HTTPStatus.CREATED)
