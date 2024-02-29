from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from aiopg.sa import SAConnection
from aiomisc import chunk_list
from datetime import datetime, date
from http import HTTPStatus
from typing import Generator, List, Dict
from sqlalchemy import insert, select

from sales.api.schema import (
    SaleSchema,
    EmptyResponseSchema,
    SaleResponseSchema,
)
from sales.db.schema import product_table, sale_table, sale_item_table
from sales.utils.pg import MAX_QUERY_ARGS, SelectQuery

from .base import BaseSaleView


class SalesView(BaseSaleView):
    URL_PATH = r"/sales"

    MAX_SALES_PER_INSERT = MAX_QUERY_ARGS // len(sale_table.columns)

    # @docs(summary="Get a list of all products")
    # @response_schema(ProductsResponseSchema(), code=HTTPStatus.OK.value)
    # async def get(self):
    #     query = product_table.select()

    #     async with self.pg.acquire() as conn:
    #         data = [self.serialize_row(row) async for row in SelectQuery(query, conn)]

    #     return web.json_response(data={"products": data})

    @docs(
        summary="Record a new sale",
        responses={
            404: {
                "description": "In items there is a product_id of a product that does not exist"
            }
        },
    )
    @request_schema(SaleSchema())
    @response_schema(SaleResponseSchema(), code=HTTPStatus.CREATED.value)
    async def post(self):
        data = await self.request.json()

        async with self.pg.acquire() as conn:
            """
            Important:
                Generated record has amount field equal to 0.
                Call `SalesView.make_select_table_rows(sale_items, sale_id, conn)`
                to update amount value.
            """
            query = (
                sale_table.insert()
                .values(
                    {
                        "date": self.convert_client_date(data.get("date")),
                        "amount": 0,
                    }
                )
                .returning(sale_table.c.sale_id)
            )
            result = await conn.execute(query)
            sale_id = await result.scalar()

        amount = await self.update_sale(data, sale_id)

        return web.json_response(data={"amount": float(amount)})
