"""add campaigns and campaign calls

Revision ID: 20260305_camp
Revises: 20260305_mem
Create Date: 2026-03-05 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260305_camp'
down_revision = '20260305_mem'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('campaign_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('briefing', sa.Text()),
        sa.Column('target_criteria', sa.JSON()),
        sa.Column('schedule', sa.JSON()),
        sa.Column('max_concurrent_calls', sa.Integer(), server_default='3'),
        sa.Column('max_retries', sa.Integer(), server_default='2'),
        sa.Column('total_targets', sa.Integer(), server_default='0'),
        sa.Column('calls_made', sa.Integer(), server_default='0'),
        sa.Column('calls_answered', sa.Integer(), server_default='0'),
        sa.Column('calls_successful', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
    )

    op.create_table(
        'campaign_calls',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False, index=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('call_session_id', sa.String(100), sa.ForeignKey('call_sessions.id')),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('attempt_number', sa.Integer(), server_default='1'),
        sa.Column('outcome', sa.String(50)),
        sa.Column('outcome_details', sa.Text()),
        sa.Column('call_duration_seconds', sa.Integer()),
        sa.Column('scheduled_at', sa.DateTime()),
        sa.Column('called_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('campaign_calls')
    op.drop_table('campaigns')
