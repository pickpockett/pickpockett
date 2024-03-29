"""Change Source.cookies column from Text to JSON

Revision ID: 386f6fe473a2
Revises: 009ea48ed350
Create Date: 2023-09-13 00:03:30.228230

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '386f6fe473a2'
down_revision = '009ea48ed350'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.alter_column('cookies',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=False,
               existing_server_default=sa.text("'{}'"))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sources', schema=None) as batch_op:
        batch_op.alter_column('cookies',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=False,
               existing_server_default=sa.text("'{}'"))

    # ### end Alembic commands ###
