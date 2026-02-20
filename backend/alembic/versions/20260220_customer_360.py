"""Add Customer 360 and enhanced call session fields

Revision ID: 20260220_customer_360
Revises: 20260217_1200_add_business_templates_and_models
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '20260220_customer_360'
down_revision = '20260217_1200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create customers table for Customer 360
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('preferred_language', sa.String(10), default='en'),
        
        # Engagement metrics
        sa.Column('total_calls', sa.Integer(), default=0),
        sa.Column('total_orders', sa.Integer(), default=0),
        sa.Column('total_appointments', sa.Integer(), default=0),
        sa.Column('total_spent', sa.Numeric(10, 2), default=0.0),
        
        # Satisfaction metrics
        sa.Column('avg_sentiment', sa.Numeric(3, 2), nullable=True),
        sa.Column('avg_quality_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('last_satisfaction_prediction', sa.Numeric(3, 2), nullable=True),
        
        # Loyalty & Risk
        sa.Column('customer_since', sa.DateTime(), nullable=True),
        sa.Column('last_interaction', sa.DateTime(), nullable=True),
        sa.Column('loyalty_tier', sa.String(20), default='standard'),
        sa.Column('churn_risk', sa.Numeric(3, 2), nullable=True),
        sa.Column('is_vip', sa.Boolean(), default=False),
        
        # Preferences
        sa.Column('preferred_contact_method', sa.String(20), nullable=True),
        sa.Column('communication_preferences', JSONB, nullable=True),
        
        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', JSONB, nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_phone', 'customers', ['phone'])
    op.create_index('ix_customers_business_id', 'customers', ['business_id'])
    
    # Add new columns to call_sessions
    op.add_column('call_sessions', sa.Column('detected_language', sa.String(10), nullable=True))
    op.add_column('call_sessions', sa.Column('quality_score', sa.Numeric(5, 2), nullable=True))
    op.add_column('call_sessions', sa.Column('satisfaction_prediction', sa.Numeric(3, 2), nullable=True))
    op.add_column('call_sessions', sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=True))
    
    # Add customer_id to orders
    op.add_column('orders', sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=True))
    
    # Add customer_id and no-show prediction to appointments
    op.add_column('appointments', sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=True))
    op.add_column('appointments', sa.Column('no_show_probability', sa.Numeric(3, 2), nullable=True))
    op.add_column('appointments', sa.Column('reminder_sent', sa.Boolean(), default=False))
    op.add_column('appointments', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove appointment columns
    op.drop_column('appointments', 'notes')
    op.drop_column('appointments', 'reminder_sent')
    op.drop_column('appointments', 'no_show_probability')
    op.drop_column('appointments', 'customer_id')
    
    # Remove order columns
    op.drop_column('orders', 'customer_id')
    
    # Remove call_session columns
    op.drop_column('call_sessions', 'customer_id')
    op.drop_column('call_sessions', 'satisfaction_prediction')
    op.drop_column('call_sessions', 'quality_score')
    op.drop_column('call_sessions', 'detected_language')
    
    # Drop customers table
    op.drop_index('ix_customers_business_id')
    op.drop_index('ix_customers_phone')
    op.drop_table('customers')
