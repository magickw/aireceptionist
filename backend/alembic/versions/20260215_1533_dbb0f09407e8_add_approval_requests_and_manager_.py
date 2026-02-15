"""Add approval requests and manager actions tables

Revision ID: dbb0f09407e8
Revises: 20260215_1411_4550b31fe1b0
Create Date: 2026-02-15 15:33:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dbb0f09407e8'
down_revision = '4550b31fe1b0'
branch_labels = None
depends_on = None


def upgrade():
    # Create approval_requests table
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=True),
        sa.Column('call_session_id', sa.String(length=100), nullable=True),
        sa.Column('request_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('action_taken', sa.String(length=100), nullable=True),
        sa.Column('requested_by', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('original_response', sa.Text(), nullable=True),
        sa.Column('final_response', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSON(), nullable=True),
        sa.Column('request_metadata', postgresql.JSON(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['call_session_id'], ['call_sessions.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_requests_id'), 'approval_requests', ['id'], unique=False)

    # Create manager_actions table
    op.create_table(
        'manager_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('approval_request_id', sa.Integer(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approval_requests.id'], ),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manager_actions_id'), 'manager_actions', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_manager_actions_id'), table_name='manager_actions')
    op.drop_table('manager_actions')
    op.drop_index(op.f('ix_approval_requests_id'), table_name='approval_requests')
    op.drop_table('approval_requests')