"""Add business_license to businesses

Revision ID: 5f3ff61738d1
Revises: 06e159e4634e
Create Date: 2026-02-14 18:13:04.176233

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5f3ff61738d1'
down_revision = '06e159e4634e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add menu_items table
    op.create_table('menu_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('available', sa.Boolean(), nullable=True),
    sa.Column('dietary_info', sa.JSON(), nullable=True),
    sa.Column('image_url', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_items_id'), 'menu_items', ['id'], unique=False)
    op.add_column('businesses', sa.Column('business_license', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('businesses', 'business_license')
    op.drop_index(op.f('ix_menu_items_id'), table_name='menu_items')
    op.drop_table('menu_items')