"""
    Resource `View` base classes
"""

from aiohttp import web
from aiopg import Pool
from aiopg.sa import SAConnection
from aiopg.sa.result import RowProxy
from datetime import date, datetime
from decimal import Decimal

from sales.db.schema import product_table, sale_table, sale_item_table


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


class BaseSaleView(BaseView):
    async def get_product(self, product_id: int, conn: SAConnection) -> float:
        query = product_table.select().where(product_table.c.product_id == product_id)
        result = await conn.execute(query)
        product = await result.fetchone()

        if not product:
            raise web.HTTPNotFound

        return product

    @classmethod
    def convert_client_date(cls, date: date) -> datetime:
        return datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")

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
                    amount += product.price * item.get("quantity")

                    query = sale_item_table.insert().values(
                        {
                            "sale_id": sale_id,
                            "product_id": product.product_id,
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

        return amount
