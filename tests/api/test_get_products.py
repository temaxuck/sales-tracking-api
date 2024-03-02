import pytest

from typing import Tuple, List
from sqlalchemy.engine import Connection

from sales.db.schema import product_table
from sales.utils.testing import (
    RecordType,
    generate_products,
    compare_products,
    get_products_data,
)


DATASETS: Tuple[List[RecordType], ...] = (
    # No products in database
    # Handler should respond with empty list of products
    [],
    # There are products in database
    # Handler should respond with valid list of products
    generate_products(4),
)


def import_dataset(connection: Connection, products: List[RecordType]) -> None:
    if products:
        query = product_table.insert().values(products)
        connection.execute(query)


@pytest.mark.asyncio
@pytest.mark.parametrize("dataset", DATASETS)
async def test_get_proudcts(api_client, migrated_postgres_connection, dataset):
    import_dataset(migrated_postgres_connection, dataset)

    actual_products = await get_products_data(api_client)
    assert compare_products(dataset, actual_products)
