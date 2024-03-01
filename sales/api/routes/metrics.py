from aiohttp import web
from aiohttp_apispec import docs, response_schema
from http import HTTPStatus
from sqlalchemy import select, func, extract
from typing import List, Dict


from sales.api.schema import (
    SaleSchema,
)
from sales.db.schema import sale_table
from sales.utils.pg import SelectQuery

from .base import BaseSaleView


class MetricsView(BaseSaleView):
    URL_PATH = r"/sales/metrics"

    def format_sales_trends(self, sales_trends: List) -> Dict:
        result = {}
        for sales_trend in sales_trends:
            result.update({int(sales_trend["year"]): sales_trend["total_sales"]})

        return result

    @docs(
        summary="Get metrics details. Use parameters start_date=dd.mm.yyyy and/or end_date=dd.mm.yyyy to set interval"
    )
    @response_schema(SaleSchema(), code=HTTPStatus.OK.value)
    async def get(self):
        params = self.request.rel_url.query
        start_date, end_date = (
            params.get("start_date"),
            params.get("end_date"),
        )

        async with self.pg.acquire() as conn:
            query = select(
                [
                    func.sum(sale_table.c.amount).label("total_sales"),
                    func.avg(sale_table.c.amount).label("average_sales"),
                ]
            ).select_from(sale_table)

            query = self.filter_select_query_by_date(start_date, end_date, query)

            result = await conn.execute(query)
            total_sales, average_sales = self.serialize_row(
                await result.fetchone()
            ).values()

            query = (
                select(
                    [
                        extract("year", sale_table.c.date).label("year"),
                        func.sum(sale_table.c.amount).label("total_sales"),
                    ]
                )
                .select_from(sale_table)
                .group_by("year")
            )

            query = self.filter_select_query_by_date(start_date, end_date, query)
            result = await conn.execute(query)
            sales_trends = [
                self.serialize_row(row) async for row in SelectQuery(query, conn)
            ]

        return web.json_response(
            data={
                "total_sales": total_sales,
                "average_sales": average_sales,
                "sales_trends": self.format_sales_trends(sales_trends),
            }
        )
