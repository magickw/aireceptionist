"""Add CallRecording and TeamMember models

Revision ID: 20260220_team_recording
Revises: 20260220_customer_360
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '20260220_team_recording'
down_revision = '20260220_customer_360'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create call_recordings table
    op.create_table(
        'call_recordings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('call_session_id', sa.String(100), sa.ForeignKey('call_sessions.id')),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False),
        sa.Column('recording_key', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        
        # Transcription
        sa.Column('transcript_key', sa.String(255), nullable=True),
        sa.Column('transcript_job_name', sa.String(255), nullable=True),
        sa.Column('transcript_status', sa.String(20), nullable=True),
        
        # Compliance
        sa.Column('consent_type', sa.String(20), default='none'),
        sa.Column('consent_obtained_at', sa.DateTime(), nullable=True),
        sa.Column('consent_method', sa.String(20), nullable=True),
        sa.Column('compliance_region', sa.String(10), default='US'),
        sa.Column('encryption_enabled', sa.Boolean(), default=True),
        
        # Deletion tracking
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deletion_reason', sa.Text(), nullable=True),
        
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_call_recordings_business_id', 'call_recordings', ['business_id'])
    op.create_index('ix_call_recordings_call_session_id', 'call_recordings', ['call_session_id'])
    
    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('role', sa.String(50), default='staff'),
        sa.Column('department', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), default='active'),
        
        # Performance metrics
        sa.Column('calls_handled', sa.Integer(), default=0),
        sa.Column('avg_quality_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('avg_satisfaction', sa.Numeric(3, 2), nullable=True),
        
        # Schedule
        sa.Column('weekly_hours', JSONB, nullable=True),
        sa.Column('timezone', sa.String(50), default='UTC'),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_team_members_business_id', 'team_members', ['business_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    
    # Add accounting invoice ID to orders
    op.add_column('orders', sa.Column('accounting_invoice_id', sa.String(100), nullable=True))
    op.add_column('orders', sa.Column('quickbooks_invoice_id', sa.String(100), nullable=True))


def downgrade() -> None:
    # Remove order columns
    op.drop_column('orders', 'quickbooks_invoice_id')
    op.drop_column('orders', 'accounting_invoice_id')
    
    # Drop team_members table
    op.drop_index('ix_team_members_user_id')
    op.drop_index('ix_team_members_business_id')
    op.drop_table('team_members')
    
    # Drop call_recordings table
    op.drop_index('ix_call_recordings_call_session_id')
    op.drop_index('ix_call_recordings_business_id')
    op.drop_table('call_recordings')
