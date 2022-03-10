"""Add Source.user_agent column

Revision ID: 9e86225b96ca
Revises: ab6b52b534af
Create Date: 2022-03-10 19:11:59.227778

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e86225b96ca'
down_revision = 'ab6b52b534af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sources', sa.Column('user_agent', sa.Text(), server_default='', nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sources', 'user_agent')
    # ### end Alembic commands ###