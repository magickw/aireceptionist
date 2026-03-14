"""Add SMS messages table

Revision ID: 20260314_add_sms_messages
Revises: 20260305_add_campaigns
Create Date: 2026-03-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260314_add_sms_messages'
down_revision = '20260305_add_campaigns'
branch_labels = None
depends_on = None


def upgrade():
    # Create sms_messages table
    op.create_table(
        'sms_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('direction', sa.String(10), nullable=False),
        sa.Column('from_number', sa.String(20), nullable=False),
        sa.Column('to_number', sa.String(20), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('media_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('twilio_sid', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='queued'),
        sa.Column('error_code', sa.String(10), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
    )
    
    # Create indexes
    op.create_index('ix_sms_messages_id', 'sms_messages', ['id'])
    op.create_index('ix_sms_messages_twilio_sid', 'sms_messages', ['twilio_sid'])
    op.create_index('ix_sms_messages_business_id', 'sms_messages', ['business_id'])
    op.create_index('ix_sms_messages_customer_id', 'sms_messages', ['customer_id'])
    op.create_index('ix_sms_messages_created_at', 'sms_messages', ['created_at'])


def downgrade():
    op.drop_index('ix_sms_messages_created_at', 'sms_messages')
    op.drop_index('ix_sms_messages_customer_id', 'sms_messages')
    op.drop_index('ix_sms_messages_business_id', 'sms_messages')
    op.drop_index('ix_sms_messages_twilio_sid', 'sms_messages')
    op.drop_index('ix_sms_messages_id', 'sms_messages')
    op.drop_table('sms_messages')
