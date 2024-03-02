from aiohttp.web_urldispatcher import DynamicResource
from aiohttp.test_utils import TestClient
from datetime import date as datetime_date, datetime
from enum import EnumMeta
from faker import Faker
from faker_vehicle import VehicleProvider
from http import HTTPStatus
from random import randint
from typing import Optional, List, Dict, Any, Union

from yarl import URL

from sales.api.routes import (
    ProductsView,
    SalesView,
    SaleView,
    MetricsView,
)
from sales.api.schema import (
    ProductsResponseSchema,
    SaleSchema,
    GetSalesResponseSchema,
    MetricsSchema,
)
from sales.config import TestConfig

RecordType = Dict[str, Any]
MAX_INTEGER = 2147483647
LONGEST_STR = "Ё" * 256
MIN_PRICE, MAX_PRICE = 3000, 8999
cfg = TestConfig()

fake = Faker()
fake.add_provider(VehicleProvider)


def serialize_date(date: datetime_date) -> str:
    return date.strftime(cfg.DATE_FORMAT)


def url_for(path: str, **kwargs) -> str:
    """
    Generate URL for dynamic aiohttp route with parameters
    """

    kwargs = {key: str(value) for key, value in kwargs.items()}

    return str(DynamicResource(path).url_for(**kwargs))


def generate_product(
    name: Optional[str] = None,
    price: Optional[float] = None,
) -> RecordType:
    """
    Create and return product data
    Auto fill not specified fields
    """
    if name is None:
        name = fake.vehicle_year_make_model()

    if price is None:
        price = randint(MIN_PRICE, MAX_PRICE) + randint(0, 99) / 100

    return {
        "name": name,
        "price": price,
    }


def generate_products(
    products_number: int, price: Optional[float] = None
) -> List[RecordType]:
    f"""
    Generate list of products 

    :param products_number: Number of products to generate
    :param price: Fixed price for all products. If not specified value in range {(MIN_PRICE, MAX_PRICE+1)} is chosen
    """
    products = []
    for _ in range(products_number):
        products.append(generate_product(price=price))

    return products


def generate_sale(
    date: Optional[datetime_date] = None,
    products: Optional[List[RecordType]] = None,
) -> RecordType:
    """
    Generate sale data.

    If products are specified, make sure they have been inserted in database.
    Quantity for each product is going to be equal to 1

    :param date: Date object representing sale date
    :param products: List of product records. If not specified, `items` is going to be an empty list
    """
    items = []

    if not date:
        date = datetime.now()

    if products:
        for product in products:
            items.append(
                {
                    "product_id": product.get("product_id"),
                    "quantity": 1,
                }
            )

    return {
        "date": serialize_date(date),
        "items": items,
    }


# def generate_sales(
#     sales_number: int,
#     date: Optional[datetime_date] = None,
#     products: Optional[List[RecordType]] = None,
# ) -> List[RecordType]:
#     f"""
#     Generate list of sales

#     :param sales_number: Number of sales to generate
#     :param price: Fixed price for all products. If not specified value in range ({MIN_PRICE, MAX_PRICE+1}) is chosen
#     """
#     products = []
#     for _ in range(sales_number):
#         products.append(generate_product(price=price))


def random_date():
    return datetime.strptime(fake.date(), "%Y-%m-%d").strftime("%d.%m.%Y")


def compare_products(
    expected_products: List[RecordType],
    actual_products: List[RecordType],
) -> bool:
    for a, b in zip(expected_products, actual_products):
        if a["name"] != b["name"] or a["price"] != b["price"]:
            return False

    return True


def compare_sales(
    expected_sales: List[RecordType],
    actual_sales: List[RecordType],
) -> bool:
    for a, b in zip(expected_sales, actual_sales):
        if a["date"] != b["date"] or a["items"] != b["items"]:
            return False

    return True


async def post_products_data(
    client: TestClient,
    products: List[RecordType],
    expected_status: Union[int, EnumMeta] = HTTPStatus.CREATED,
    **request_kwargs,
) -> None:
    response = await client.post(
        ProductsView.URL_PATH,
        json={"products": products},
        **request_kwargs,
    )

    assert response.status == expected_status


async def get_products_data(
    client: TestClient,
    expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
    **request_kwargs,
) -> List[RecordType]:
    response = await client.get(
        ProductsView.URL_PATH,
        **request_kwargs,
    )

    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = ProductsResponseSchema().validate(data)
        assert errors == {}
        return data["products"]


async def post_sales_data(
    client: TestClient,
    date: datetime_date,
    items: List[RecordType],
    expected_status: Union[int, EnumMeta] = HTTPStatus.CREATED,
    **request_kwargs,
) -> RecordType:
    response = await client.post(
        SalesView.URL_PATH,
        json={
            "date": date,
            "items": items,
        },
        **request_kwargs,
    )

    assert response.status == expected_status

    if response.status == HTTPStatus.CREATED:
        data = await response.json()
        errors = SaleSchema().validate(data)
        assert errors == {}
        return data


async def get_sales_data(
    client: TestClient,
    start_date: str = None,
    end_date: str = None,
    expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
    **request_kwargs,
) -> RecordType:
    """
    BUG: without below call server responds with 500 Internal error.
    """
    response = await client.get(
        ProductsView.URL_PATH,
        **request_kwargs,
    )

    params = {}

    if start_date:
        params.update({"start_date": start_date})

    if end_date:
        params.update({"end_date": end_date})

    response = await client.get(
        URL(SalesView.URL_PATH) % params,
        **request_kwargs,
    )

    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = GetSalesResponseSchema().validate(data)
        assert errors == {}
        return data["sales"]


async def get_sale_data(
    client: TestClient,
    sale_id: int,
    expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
    **request_kwargs,
) -> RecordType:
    response = await client.get(
        url_for(SaleView.URL_PATH, sale_id=sale_id),
        **request_kwargs,
    )

    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = SaleSchema().validate(data)
        assert errors == {}
        return data


async def put_sale_data(
    client: TestClient,
    sale_id: int,
    new_date: str,
    new_items: List[RecordType],
    expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
    **request_kwargs,
) -> RecordType:
    response = await client.put(
        url_for(SaleView.URL_PATH, sale_id=sale_id),
        json={"date": new_date, "items": new_items},
        **request_kwargs,
    )

    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = SaleSchema().validate(data)
        assert errors == {}
        return data


async def get_sales_metrics_data(
    client: TestClient,
    start_date: str = None,
    end_date: str = None,
    expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
    **request_kwargs,
) -> RecordType:
    params = {}

    if start_date:
        params.update({"start_date": start_date})

    if end_date:
        params.update({"end_date": end_date})

    response = await client.get(
        URL(MetricsView.URL_PATH) % params,
        **request_kwargs,
    )

    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = MetricsSchema().validate(data)
        assert errors == {}
        return data
