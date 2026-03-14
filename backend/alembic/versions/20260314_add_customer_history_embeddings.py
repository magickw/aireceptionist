"""Add customer_history_embeddings table

Revision ID: 20260314_embeddings
Revises: 20260314_add_sms_messages
Create Date: 2026-03-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import VECTOR

# revision identifiers, used by Alembic.
revision = '20260314_embeddings'
down_revision = '20260314_add_sms_messages'
branch_labels = None
depends_on = None


def upgrade():
    # Create customer_history_embeddings table
    op.create_table(
        'customer_history_embeddings',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False),
        sa.Column('customer_phone', sa.String(20), nullable=False, index=True),
        sa.Column('call_session_id', sa.Integer(), sa.ForeignKey('call_sessions.id')),
        sa.Column('conversation_text', sa.Text(), nullable=False),
        sa.Column('embedding', VECTOR(1536)),  # Titan embedding dimensions
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Create indexes for faster lookups
    op.create_index('ix_customer_history_embeddings_business_phone', 'customer_history_embeddings', 
                    ['business_id', 'customer_phone'])
    op.create_index('ix_customer_history_embeddings_session', 'customer_history_embeddings', 
                    ['call_session_id'])


def downgrade():
    op.drop_index('ix_customer_history_embeddings_session')
    op.drop_index('ix_customer_history_embeddings_business_phone')
    op.drop_table('customer_history_embeddings')
