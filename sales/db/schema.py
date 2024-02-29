from enum import Enum, unique
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    ForeignKey,
    String,
    Numeric,
    Date,
    Enum as pgEnum,
    ForeignKeyConstraint,
)


# Naming Convention for tables and constraints
convention = {
    "all_column_names": lambda constraint, table: "_".join(
        [column.name for column in constraint.columns.values()]
    ),
    # index naming
    "ix": "ix__%(table_name)s_%(all_column_names)s",
    # unique index naming
    "uq": "uq__%(table_name)s_%(all_column_names)s",
    # check constraints naming
    "ck": "ck__%(table_name)s_%(constarint_name)s",
    # foreign key constraint naming
    "fk": "fk__%(table_name)s_%(all_column_names)s_%(referred_table_name)s",
    # primary key constraint naming
    "pk": "pk__%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

sale_table = Table(
    "sale",
    metadata,
    Column("sale_id", Integer, primary_key=True),
    Column("date", Date, nullable=False),
    Column("amount", Numeric, nullable=False),
)

product_table = Table(
    "product",
    metadata,
    Column("product_id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("price", Numeric, nullable=False),
)

sale_item_table = Table(
    "sale_item",
    metadata,
    Column("sales_id", Integer, ForeignKey("sales.sale_id"), primary_key=True),
    Column("product_id", Integer, ForeignKey("products.product_id"), primary_key=True),
    # Numeric for a case, when product is not discret
    Column("quantity", Numeric, nullable=False),
)
