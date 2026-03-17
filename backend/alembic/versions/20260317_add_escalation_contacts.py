"""Add escalation contact fields to businesses

Revision ID: 20260317_escalation
Revises: 20260314_embeddings
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260317_escalation'
down_revision = '20260314_embeddings'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Add escalation contact fields to businesses table
    # Use try/except to handle case where columns might already exist
    columns_to_add = [
        ('emergency_contact_name', sa.String(255)),
        ('emergency_contact_phone', sa.String(20)),
        ('emergency_contact_email', sa.String(255)),
        ('secondary_contact_name', sa.String(255)),
        ('secondary_contact_phone', sa.String(20)),
        ('escalation_priority', sa.String(20)),
    ]
    
    for col_name, col_type in columns_to_add:
        if not column_exists('businesses', col_name):
            try:
                op.add_column('businesses', sa.Column(col_name, col_type, nullable=True))
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Warning: Could not add column {col_name}: {e}")
        else:
            print(f"Column already exists: {col_name}")


def downgrade():
    columns_to_drop = [
        'escalation_priority',
        'secondary_contact_phone',
        'secondary_contact_name',
        'emergency_contact_email',
        'emergency_contact_phone',
        'emergency_contact_name',
    ]
    
    for col_name in columns_to_drop:
        if column_exists('businesses', col_name):
            try:
                op.drop_column('businesses', col_name)
                print(f"Dropped column: {col_name}")
            except Exception as e:
                print(f"Warning: Could not drop column {col_name}: {e}")