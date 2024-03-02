import pytest
import pytz

from copy import copy
from datetime import datetime, timedelta
from http import HTTPStatus
from numbers import Number
from typing import Union, Tuple, Mapping, List
from random import randint
from unittest.mock import patch

from sales.config import TestConfig
from sales.utils.testing import (
    LONGEST_STR,
    MAX_INTEGER,
    RecordType,
    generate_product,
    generate_products,
    compare_products,
    post_products_data,
    get_products_data,
)

cfg = TestConfig()

TestCaseType = Tuple[List[RecordType], HTTPStatus]

CASES: Tuple[TestCaseType, ...] = (
    # ==== POSITIVE TESTCASES ====
    # Post valid list of products
    # Handler is expected to create and save products
    (
        generate_products(4),
        HTTPStatus.CREATED,
    ),
    # Post empty list of products
    # Handler is expected to not break and respond with CREATED status
    (
        [],
        HTTPStatus.CREATED,
    ),
    # Post a product with name equal to longest valid string
    # Handler is expected to not break and respond with CREATED status
    (
        [generate_product(name=LONGEST_STR)],
        HTTPStatus.CREATED,
    ),
    # Post a product with price equal to 0
    # Handler is expected to not break and respond with CREATED status
    (
        [generate_product(price=0)],
        HTTPStatus.CREATED,
    ),
    # Post a produict with price equal to MAX_INTEGER
    # Handler is expected to not break and respond with CREATED status
    (
        [generate_product(price=MAX_INTEGER)],
        HTTPStatus.CREATED,
    ),
    # ==== NEGATIVE TESTCASES ====
    # Post a product with an empty name
    # Handler is expected to respond with BAD_REQUEST status
    (
        [generate_product(name="")],
        HTTPStatus.BAD_REQUEST,
    ),
    # Post a product with too long string as name
    # Handler is expected to respond with BAD_REQUEST status
    (
        [generate_product(name=LONGEST_STR + "Ё")],
        HTTPStatus.BAD_REQUEST,
    ),
    # Post a product with a negative price
    # Handler is expected to respond with BAD_REQUEST status
    (
        [generate_product(price=-100)],
        HTTPStatus.BAD_REQUEST,
    ),
    # Post an empty product
    # Handler is expected to respond with BAD_REQUEST status
    (
        [{}],
        HTTPStatus.BAD_REQUEST,
    ),
)


@pytest.mark.asyncio
@pytest.mark.parametrize("products, expected_status", CASES)
async def test_post_proudcts(api_client, products, expected_status):
    await post_products_data(api_client, products, expected_status)

    if expected_status == HTTPStatus.CREATED:
        actual_products = await get_products_data(api_client)
        assert compare_products(products, actual_products)
