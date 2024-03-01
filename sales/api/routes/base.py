"""
    Resource `View` base classes
"""

from aiohttp import web
from aiopg import Pool
from aiopg.sa import SAConnection
from aiopg.sa.result import RowProxy
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.sql import Select
from sqlalchemy import and_

from sales.db.schema import product_table, sale_table, sale_item_table
from sales.api.middleware import format_http_error


class BaseView(web.View):
    URL_PATH: str

    @property
    def app(self) -> web.Application:
        return self.request.app

    @property
    def pg(self) -> Pool:
        return self.request.app["pg"]

    def serialize_row(self, row: RowProxy) -> dict:
        row = dict(row)

        for k, v in row.items():
            if isinstance(v, date):
                row[k] = v.strftime(self.app["config"].DATE_FORMAT)
            if isinstance(v, Decimal):
                row[k] = float(v)

        return row

    @classmethod
    def convert_client_date(self, date: date) -> datetime:
        try:
            return datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            raise format_http_error(
                web.HTTPBadRequest,
                "specified date parameter is not a valid date",
            )


class BaseSaleView(BaseView):

    def filter_select_query_by_date(
        self,
        start_date: str,
        end_date: str,
        query: Select,
    ) -> Select:
        if end_date and not start_date:
            raise format_http_error(
                web.HTTPBadRequest,
                "end_date parameter is specified but start_date is not.",
            )

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

        return query

    async def check_if_sale_exists(self, sale_id: int) -> None:
        async with self.pg.acquire() as conn:
            query = sale_table.select().where(sale_table.c.sale_id == sale_id)
            result = await conn.execute(query)
            sale = await result.fetchone()

            if not sale:
                raise web.HTTPNotFound

    async def get_product(self, product_id: int, conn: SAConnection) -> float:
        query = product_table.select().where(product_table.c.product_id == product_id)
        result = await conn.execute(query)
        product = await result.fetchone()

        if not product:
            raise web.HTTPNotFound

        return product

    async def update_sale(self, data: dict, sale_id: int) -> int:
        amount = 0
        async with self.pg.acquire() as conn:
            async with conn.begin() as _:
                query = sale_item_table.delete().where(
                    sale_item_table.c.sale_id == sale_id
                )
                await conn.execute(query)

                for item in data.get("items"):
                    product = await self.get_product(item.get("product_id"), conn)

                    amount += product.get("price") * Decimal(item.get("quantity"))

                    query = sale_item_table.insert().values(
                        {
                            "sale_id": sale_id,
                            "product_id": product.get("product_id"),
                            "quantity": item.get("quantity"),
                        }
                    )
                    await conn.execute(query)

                query = (
                    sale_table.update()
                    .where(sale_table.c.sale_id == sale_id)
                    .values(
                        date=self.convert_client_date(data.get("date")),
                        amount=amount,
                    )
                )
                await conn.execute(query)

        data.update({"sale_id": sale_id})
        data.update({"amount": amount})
        return data
