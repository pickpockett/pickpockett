"""Create table 'sources'

Revision ID: ab6b52b534af
Revises: 
Create Date: 2022-02-15 02:32:33.349432

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab6b52b534af'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sources',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tvdb_id', sa.Integer(), nullable=False),
    sa.Column('season', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('url', sa.Text(), nullable=False),
    sa.Column('cookies', sa.Text(), server_default='', nullable=False),
    sa.Column('hash', sa.String(length=40), server_default='', nullable=False),
    sa.Column('datetime', sa.DateTime(), nullable=True),
    sa.Column('quality', sa.Text(), nullable=False),
    sa.Column('language', sa.Text(), server_default='', nullable=False),
    sa.Column('error', sa.Text(), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sources')
    # ### end Alembic commands ###
