import pytest

from aiohttp.test_utils import TestClient
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import List
from sqlalchemy.engine import Connection

from sales.db.schema import (
    product_table,
)
from sales.utils.testing import (
    MAX_INTEGER,
    RecordType,
    random_date,
    generate_product,
    compare_sales,
    get_sales_data,
    post_sales_data,
    get_products_data,
)

"""
Positive:
    - standard query
    - only start_date
    - only end_date
    - both start_date and end_date
    - no sales in database
Negative:
    - start_date is wrong format
"""


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

    expected_sales = []

    date = "25.12.2020"
    items = [
        {"product_id": product["product_id"], "quantity": 1}
        for product in actual_products
    ]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)

    date = "25.12.2021"
    items = [{"product_id": actual_products[0]["product_id"], "quantity": 1}]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)

    date = "25.12.2022"
    items = [{"product_id": actual_products[1]["product_id"], "quantity": 1}]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)

    date = "25.12.2023"
    items = [{"product_id": actual_products[2]["product_id"], "quantity": 1}]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)

    return expected_sales


@pytest.mark.asyncio
async def test_get_sales(api_client, migrated_postgres_connection):
    expected_sales = await setup_test(api_client, migrated_postgres_connection)
    actual_sales = await get_sales_data(api_client)

    assert len(expected_sales) == len(actual_sales)
    assert compare_sales(expected_sales, actual_sales)


@pytest.mark.asyncio
async def test_get_sales_with_params(api_client, migrated_postgres_connection):
    expected_sales = await setup_test(api_client, migrated_postgres_connection)
    actual_sales = await get_sales_data(api_client, start_date="25.12.2021")

    print(actual_sales)

    assert len(actual_sales) == 3
    assert compare_sales(expected_sales[1:], actual_sales)

    actual_sales = await get_sales_data(api_client, end_date="25.12.2021")

    assert len(actual_sales) == 2
    assert compare_sales(expected_sales[:2], actual_sales)

    actual_sales = await get_sales_data(
        api_client, start_date="25.12.2021", end_date="25.12.2021"
    )

    assert len(actual_sales) == 1
    assert compare_sales(expected_sales[1:2], actual_sales)

    actual_sales = await get_sales_data(
        api_client,
        start_date="25-12.2021",
        end_date="25.12.2021",
        expected_status=HTTPStatus.BAD_REQUEST,
    )
