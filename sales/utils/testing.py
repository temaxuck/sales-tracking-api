from aiohttp.typedefs import StrOrURL
from aiohttp.web_urldispatcher import DynamicResource
from aiohttp.test_utils import TestClient
from enum import EnumMeta
from faker import Faker
from http import HTTPStatus
from random import randint, choice, shuffle
from typing import Optional, List, Dict, Any, Mapping, Iterable, Union

# from sales.api.routes import ()
# from sales.api.schema import
from sales.config import TestConfig

CitizenType = Dict[str, Any]
MAX_INTEGER = 2147483647
cfg = TestConfig()

fake = Faker(["ru_RU", "en_US"])


def url_for(path: str, **kwargs) -> str:
    """
    Generate URL for dynamic aiohttp route with parameters
    """

    kwargs = {key: str(value) for key, value in kwargs.items()}

    return str(DynamicResource(path).url_for(**kwargs))
