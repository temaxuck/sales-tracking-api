"""Change column name from sales_id to sale_id

Revision ID: eb845e995f33
Revises: 7218198efdaa
Create Date: 2024-02-29 15:23:20.334469

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "eb845e995f33"
down_revision: Union[str, None] = "7218198efdaa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("sale_item", sa.Column("sale_id", sa.Integer(), nullable=False))
    op.drop_constraint("fk__sale_item_sales_id_sale", "sale_item", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk__sale_item_sale_id_sale"),
        "sale_item",
        "sale",
        ["sale_id"],
        ["sale_id"],
    )
    op.drop_column("sale_item", "sales_id")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "sale_item",
        sa.Column("sales_id", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(
        op.f("fk__sale_item_sale_id_sale"), "sale_item", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk__sale_item_sales_id_sale", "sale_item", "sale", ["sales_id"], ["sale_id"]
    )
    op.drop_column("sale_item", "sale_id")
    # ### end Alembic commands ###
