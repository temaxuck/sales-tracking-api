from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from http import HTTPStatus
from sqlalchemy import select

from sales.api.schema import (
    BaseSaleSchema,
    GetSaleResponseSchema,
    SaleSchema,
)
from sales.db.schema import sale_table, sale_item_table
from sales.utils.pg import SelectQuery

from .base import BaseSaleView


class SalesView(BaseSaleView):
    URL_PATH = r"/sales"

    @docs(summary="Get a list of all sales")
    @response_schema(GetSaleResponseSchema(), code=HTTPStatus.OK.value)
    async def get(self):
        params = self.request.rel_url.query
        start_date, end_date = (
            params.get("start_date"),
            params.get("end_date"),
        )

        async with self.pg.acquire() as conn:
            query = self.filter_select_query_by_date(
                start_date,
                end_date,
                sale_table.select(),
            )

            sales = [self.serialize_row(row) async for row in SelectQuery(query, conn)]
            for sale in sales:
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

        return web.json_response(data={"sales": sales})

    @docs(
        summary="Record a new sale",
        responses={
            404: {
                "description": "In items there is a product_id of a product that does not exist"
            }
        },
    )
    @request_schema(BaseSaleSchema())
    @response_schema(SaleSchema(), code=HTTPStatus.CREATED.value)
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

        sale = await self.update_sale(data, sale_id)

        return web.json_response(
            data=self.serialize_row(sale), status=HTTPStatus.CREATED.value
        )
