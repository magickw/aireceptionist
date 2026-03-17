"""Add escalations table for state machine tracking

Revision ID: 20260317_escalations
Revises: 20260317_escalation
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '20260317_escalations'
down_revision = '20260317_escalation'
branch_labels = None
depends_on = None


def upgrade():
    # Create escalations table
    op.create_table(
        'escalations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('call_session_id', sa.String(100), nullable=True),
        
        # State machine
        sa.Column('state', sa.String(20), nullable=False, server_default='triggered'),
        
        # Escalation details
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), server_default='medium'),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('context', JSON, nullable=True),
        
        # Customer info
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('customer_name', sa.String(255), nullable=True),
        
        # Notification tracking
        sa.Column('notified_contacts', JSON, nullable=True),
        sa.Column('notification_channels', JSON, nullable=True),
        
        # Acknowledgment tracking
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledgment_notes', sa.Text(), nullable=True),
        
        # Resolution tracking
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolution_action', sa.String(50), nullable=True),
        
        # SLA tracking
        sa.Column('sla_deadline', sa.DateTime(), nullable=True),
        sa.Column('sla_breached', sa.Boolean(), server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.ForeignKeyConstraint(['call_session_id'], ['call_sessions.id']),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
    )
    
    # Create indexes
    op.create_index('ix_escalations_id', 'escalations', ['id'])
    op.create_index('ix_escalations_state', 'escalations', ['state'])
    op.create_index('ix_escalations_created_at', 'escalations', ['created_at'])
    op.create_index('ix_escalations_business_id', 'escalations', ['business_id'])


def downgrade():
    op.drop_index('ix_escalations_business_id', 'escalations')
    op.drop_index('ix_escalations_created_at', 'escalations')
    op.drop_index('ix_escalations_state', 'escalations')
    op.drop_index('ix_escalations_id', 'escalations')
    op.drop_table('escalations')
