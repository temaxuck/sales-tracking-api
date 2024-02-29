from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema
from http import HTTPStatus
from sqlalchemy import and_, select

from sales.api.schema import (
    BaseSaleSchema,
    GetSaleResponseSchema,
    PostSaleResponseSchema,
)
from sales.api.middleware import format_http_error
from sales.db.schema import sale_table, sale_item_table
from sales.utils.pg import MAX_QUERY_ARGS, SelectQuery

from .base import BaseSaleView


class SalesView(BaseSaleView):
    URL_PATH = r"/sales"

    MAX_SALES_PER_INSERT = MAX_QUERY_ARGS // len(sale_table.columns)

    @docs(summary="Get a list of all products")
    @response_schema(GetSaleResponseSchema(), code=HTTPStatus.OK.value)
    async def get(self):
        params = self.request.rel_url.query
        start_date, end_date = (
            params.get("start_date"),
            params.get("end_date"),
        )

        if end_date and not start_date:
            raise format_http_error(
                web.HTTPBadRequest,
                "end_date parameter is specified but start_date is not.",
            )

        async with self.pg.acquire() as conn:
            query = sale_table.select()

            if start_date:

                start_date = self.convert_client_date(start_date)
                if end_date:
                    end_date = self.convert_client_date(end_date)
                    query = query.where(
                        and_(
                            sale_table.c.date >= start_date,
                            sale_table.c.date <= end_date,
                        )
                    )
                else:
                    query = query.where(sale_table.c.date >= start_date)

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
    @response_schema(PostSaleResponseSchema(), code=HTTPStatus.CREATED.value)
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
