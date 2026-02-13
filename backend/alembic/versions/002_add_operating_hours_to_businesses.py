"""Add operating_hours column to businesses table

Revision ID: 002_add_operating_hours
Revises: 001_initial
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_operating_hours'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('businesses', sa.Column('operating_hours', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('businesses', 'operating_hours')