"""add customer memories and call summaries v2

Revision ID: 20260305_mem
Revises: 20260227_lang
Create Date: 2026-03-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260305_mem'
down_revision = '20260227_lang'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'customer_memories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False, index=True),
        sa.Column('memory_type', sa.String(50), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.DECIMAL(3, 2), server_default='1.0'),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('source_session_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'call_summaries_v2',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('call_session_id', sa.String(100), sa.ForeignKey('call_sessions.id'), nullable=False, index=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), index=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False, index=True),
        sa.Column('summary_text', sa.Text()),
        sa.Column('key_topics', sa.JSON()),
        sa.Column('outcome', sa.String(100)),
        sa.Column('action_items', sa.JSON()),
        sa.Column('sentiment_arc', sa.String(100)),
        sa.Column('extracted_facts', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('call_summaries_v2')
    op.drop_table('customer_memories')
