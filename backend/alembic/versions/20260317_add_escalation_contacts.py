"""Add escalation contact fields to businesses

Revision ID: 20260317_escalation
Revises: 20260314_embeddings
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '20260317_escalation'
down_revision = '20260314_embeddings'
branch_labels = None
depends_on = None


def upgrade():
    # Add escalation contact fields to businesses table
    op.add_column('businesses', sa.Column('emergency_contact_name', sa.String(255), nullable=True))
    op.add_column('businesses', sa.Column('emergency_contact_phone', sa.String(20), nullable=True))
    op.add_column('businesses', sa.Column('emergency_contact_email', sa.String(255), nullable=True))
    op.add_column('businesses', sa.Column('secondary_contact_name', sa.String(255), nullable=True))
    op.add_column('businesses', sa.Column('secondary_contact_phone', sa.String(20), nullable=True))
    op.add_column('businesses', sa.Column('escalation_priority', sa.String(20), nullable=True, server_default='sms_then_push'))


def downgrade():
    op.drop_column('businesses', 'escalation_priority')
    op.drop_column('businesses', 'secondary_contact_phone')
    op.drop_column('businesses', 'secondary_contact_name')
    op.drop_column('businesses', 'emergency_contact_email')
    op.drop_column('businesses', 'emergency_contact_phone')
    op.drop_column('businesses', 'emergency_contact_name')
