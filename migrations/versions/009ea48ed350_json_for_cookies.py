"""JSON for cookies

Revision ID: 009ea48ed350
Revises: cfd3bf8c5ca3
Create Date: 2023-07-16 22:13:48.221621

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "009ea48ed350"
down_revision = "cfd3bf8c5ca3"
branch_labels = None
depends_on = None


def alter_server_default(old, new):
    database = "sources"
    column = "cookies"
    column_alter = f"{column}_alter"

    op.add_column(
        database,
        sa.Column(column_alter, sa.Text(), server_default=new, nullable=False),
    )
    sources = sa.table(
        database,
        sa.column(column, sa.Text),
        sa.column(column_alter, sa.Text),
    )
    op.execute(
        sources.update()
        .where(sources.c.cookies != op.inline_literal(old))
        .values({column_alter: sources.c.cookies})
    )
    op.drop_column(database, column)
    op.alter_column(database, column_alter, new_column_name=column)


def upgrade():
    alter_server_default("", "{}")


def downgrade():
    alter_server_default("{}", "")
