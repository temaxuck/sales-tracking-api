import pytest

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
    post_sales_data,
    generate_product,
    get_products_data,
)


def import_products(connection: Connection, products: List[RecordType]) -> None:
    if products:
        query = product_table.insert().values(products).returning()
        connection.execute(query)


@pytest.mark.asyncio
async def test_valid_sale(api_client, migrated_postgres_connection):
    products = [
        generate_product(price=150),
        generate_product(price=200),
        generate_product(price=30),
    ]
    import_products(migrated_postgres_connection, products)
    actual_products = await get_products_data(api_client)

    items = [
        {"product_id": product["product_id"], "quantity": 1}
        for product in actual_products
    ]

    sale = await post_sales_data(api_client, random_date(), items, HTTPStatus.CREATED)

    assert sale["amount"] == 380


@pytest.mark.asyncio
async def test_sale_empty_items(api_client):
    items = []

    sale = await post_sales_data(api_client, random_date(), items, HTTPStatus.CREATED)

    assert sale["amount"] == 0


@pytest.mark.asyncio
async def test_sale_item_quantity_is_float(api_client, migrated_postgres_connection):
    products = [
        generate_product(price=100),
        generate_product(price=30),
    ]

    import_products(migrated_postgres_connection, products)
    actual_products = await get_products_data(api_client)

    items = [
        {"product_id": actual_products[0]["product_id"], "quantity": 1.5},
        {"product_id": actual_products[1]["product_id"], "quantity": 1},
    ]

    sale = await post_sales_data(api_client, random_date(), items, HTTPStatus.CREATED)

    assert sale["amount"] == 180


@pytest.mark.asyncio
async def test_large_quantity(api_client, migrated_postgres_connection):
    products = [generate_product(price=1)]
    import_products(migrated_postgres_connection, products)
    actual_products = await get_products_data(api_client)

    items = [
        {"product_id": actual_products[0]["product_id"], "quantity": MAX_INTEGER},
    ]

    sale = await post_sales_data(api_client, random_date(), items, HTTPStatus.CREATED)

    assert sale["amount"] == MAX_INTEGER


@pytest.mark.asyncio
async def test_invalid_date(api_client):
    items = []

    await post_sales_data(api_client, "25-12-2023", items, HTTPStatus.BAD_REQUEST)
    await post_sales_data(
        api_client,
        (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
        items,
        HTTPStatus.BAD_REQUEST,
    )


@pytest.mark.asyncio
async def test_invalid_date_format(api_client, migrated_postgres_connection):
    products = [generate_product(price=100)]
    import_products(migrated_postgres_connection, products)
    actual_products = await get_products_data(api_client)

    items = [
        {"product_id": actual_products[0]["product_id"], "quantity": 0},
    ]

    await post_sales_data(api_client, random_date(), items, HTTPStatus.BAD_REQUEST)


@pytest.mark.asyncio
async def test_non_existent_product_id(api_client, migrated_postgres_connection):
    items = [
        {"product_id": 999, "quantity": 1},
    ]

    await post_sales_data(api_client, random_date(), items, HTTPStatus.NOT_FOUND)
