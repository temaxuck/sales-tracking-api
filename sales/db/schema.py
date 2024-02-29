from enum import Enum, unique
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    ForeignKey,
    String,
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
