import pytest

from aiohttp.test_utils import TestClient
from http import HTTPStatus
from typing import List
from sqlalchemy.engine import Connection

from sales.db.schema import (
    product_table,
)
from sales.utils.testing import (
    RecordType,
    generate_product,
    compare_sales,
    get_sale_data,
    post_sales_data,
    get_products_data,
)


def import_products(connection: Connection, products: List[RecordType]) -> None:
    if products:
        query = product_table.insert().values(products).returning()
        connection.execute(query)


async def setup_test(client: TestClient, connection: Connection) -> List[RecordType]:
    products = [
        generate_product(price=150),
        generate_product(price=200),
        generate_product(price=30),
    ]
    import_products(connection, products)
    actual_products = await get_products_data(client)

    date = "25.12.2020"
    items = [
        {"product_id": product["product_id"], "quantity": 1}
        for product in actual_products
    ]
    sale = await post_sales_data(client, date, items, HTTPStatus.CREATED)

    return sale["sale_id"], {"date": date, "items": items}


@pytest.mark.asyncio
async def test_get_sale(api_client, migrated_postgres_connection):
    sale_id, expected_sale = await setup_test(api_client, migrated_postgres_connection)
    actual_sale = await get_sale_data(api_client, sale_id)

    assert compare_sales([expected_sale], [actual_sale])
