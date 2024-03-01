from .products import ProductsView
from .sales import SalesView
from .sale import SaleView
from .metrics import MetricsView

ROUTES = (
    ProductsView,
    SalesView,
    SaleView,
    MetricsView,
)
