"""
    Resource `View` base classes
"""

from aiohttp import web
from aiopg import Pool
from aiopg.sa.result import RowProxy
from datetime import date
from decimal import Decimal


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
