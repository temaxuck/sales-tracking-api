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
    get_sales_metrics_data,
    post_sales_data,
    get_products_data,
)

"""
Positive:
    - sale data is present
    - no sales 
    - valid date params
Negative:
    -invalid date_params
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
    # total_sales = 380
    items = [
        {"product_id": product["product_id"], "quantity": 1}
        for product in actual_products
    ]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)

    date = "25.12.2021"
    # total_sales = 150
    items = [{"product_id": actual_products[0]["product_id"], "quantity": 1}]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)

    date = "25.12.2022"
    # total_sales = 200
    items = [{"product_id": actual_products[1]["product_id"], "quantity": 1}]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)

    date = "25.12.2023"
    # total_sales = 30
    items = [{"product_id": actual_products[2]["product_id"], "quantity": 1}]
    expected_sales.append({"date": date, "items": items})
    await post_sales_data(client, date, items, HTTPStatus.CREATED)


@pytest.mark.asyncio
async def test_get_sales_metrics(api_client, migrated_postgres_connection):
    await setup_test(api_client, migrated_postgres_connection)
    metrics = await get_sales_metrics_data(api_client)

    assert metrics == {
        "total_sales": 760.0,
        "average_sales": 190.0,
        "sales_trends": {"2023": 30.0, "2022": 200.0, "2021": 150.0, "2020": 380.0},
    }


@pytest.mark.asyncio
async def test_get_empty_sales_metrics(api_client):
    metrics = await get_sales_metrics_data(api_client)

    assert metrics == {
        "total_sales": None,
        "average_sales": None,
        "sales_trends": {},
    }


@pytest.mark.asyncio
async def test_get_sales_metrics_with_params(api_client, migrated_postgres_connection):
    await setup_test(api_client, migrated_postgres_connection)

    metrics = await get_sales_metrics_data(api_client, start_date="01.01.2023")
    assert metrics == {
        "total_sales": 30.0,
        "average_sales": 30.0,
        "sales_trends": {"2023": 30.0},
    }

    metrics = await get_sales_metrics_data(api_client, end_date="01.01.2022")
    assert metrics == {
        "total_sales": 530.0,
        "average_sales": 265.0,
        "sales_trends": {"2021": 150.0, "2020": 380.0},
    }

    metrics = await get_sales_metrics_data(
        api_client, start_date="01.01.2021", end_date="01.01.2022"
    )
    assert metrics == {
        "total_sales": 150.0,
        "average_sales": 150.0,
        "sales_trends": {"2021": 150.0},
    }

    metrics = await get_sales_metrics_data(
        api_client, start_date="01.01.2018", end_date="01.01.2019"
    )
    assert metrics == {
        "total_sales": None,
        "average_sales": None,
        "sales_trends": {},
    }

    metrics = await get_sales_metrics_data(
        api_client,
        start_date="01-01-2021",
        end_date="01.01.2022",
        expected_status=HTTPStatus.BAD_REQUEST,
    )
