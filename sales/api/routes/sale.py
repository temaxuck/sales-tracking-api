from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from http import HTTPStatus
from sqlalchemy import select

from sales.api.schema import (
    BaseSaleSchema,
    SaleSchema,
)
from sales.db.schema import sale_table, sale_item_table
from sales.utils.pg import SelectQuery

from .base import BaseSaleView


class SaleView(BaseSaleView):
    URL_PATH = r"/sales/{sale_id:\d+}"

    @property
    def sale_id(self) -> int:
        return int(self.request.match_info.get("sale_id"))

    @docs(summary="Get details about a sale")
    @response_schema(SaleSchema(), code=HTTPStatus.OK.value)
    async def get(self):
        await self.check_if_sale_exists(self.sale_id)

        async with self.pg.acquire() as conn:
            query = sale_table.select().where(sale_table.c.sale_id == self.sale_id)
            result = await conn.execute(query)
            sale = self.serialize_row(await result.fetchone())

            query = (
                select(
                    [
                        sale_item_table.c.product_id,
                        sale_item_table.c.quantity,
                    ]
                )
                .select_from(sale_item_table)
                .where(sale_item_table.c.sale_id == sale.get("sale_id"))
            )
            sale.update(
                {
                    "items": [
                        self.serialize_row(row)
                        async for row in SelectQuery(query, conn)
                    ]
                }
            )

        return web.json_response(data=sale)

    @docs(
        summary="Change sale data",
        responses={
            404: {
                "description": "In items there is a product_id of a product that does not exist"
            }
        },
    )
    @request_schema(BaseSaleSchema())
    @response_schema(SaleSchema(), code=HTTPStatus.OK.value)
    async def put(self):
        await self.check_if_sale_exists(self.sale_id)

        data = await self.request.json()

        sale = await self.update_sale(data, self.sale_id)

        return web.json_response(data=self.serialize_row(sale))
