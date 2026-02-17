"""Add business templates, intent classification, and business type detection models

Revision ID: 20260217_1200
Revises: dbb0f09407e8
Create Date: 2026-02-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260217_1200'
down_revision = 'dbb0f09407e8'
branch_labels = None
depends_on = None


def upgrade():
    # Create business_templates table
    op.create_table(
        'business_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('autonomy_level', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('high_risk_intents', postgresql.JSON(), nullable=True),
        sa.Column('auto_escalate_threshold', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('confidence_threshold', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('common_intents', postgresql.JSON(), nullable=True),
        sa.Column('fields', postgresql.JSON(), nullable=True),
        sa.Column('booking_flow', postgresql.JSON(), nullable=True),
        sa.Column('system_prompt_addition', sa.Text(), nullable=True),
        sa.Column('example_responses', postgresql.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_key')
    )
    op.create_index(op.f('ix_business_templates_id'), 'business_templates', ['id'], unique=False)
    op.create_index(op.f('ix_business_templates_template_key'), 'business_templates', ['template_key'], unique=True)

    # Create template_versions table
    op.create_table(
        'template_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('autonomy_level', sa.String(length=20), nullable=True),
        sa.Column('high_risk_intents', postgresql.JSON(), nullable=True),
        sa.Column('auto_escalate_threshold', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('confidence_threshold', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('common_intents', postgresql.JSON(), nullable=True),
        sa.Column('fields', postgresql.JSON(), nullable=True),
        sa.Column('booking_flow', postgresql.JSON(), nullable=True),
        sa.Column('system_prompt_addition', sa.Text(), nullable=True),
        sa.Column('example_responses', postgresql.JSON(), nullable=True),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['business_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_versions_id'), 'template_versions', ['id'], unique=False)

    # Create intent_classifications table
    op.create_table(
        'intent_classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_type', sa.String(length=50), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=False),
        sa.Column('user_input', sa.Text(), nullable=False),
        sa.Column('entities', postgresql.JSON(), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intent_classifications_id'), 'intent_classifications', ['id'], unique=False)

    # Create business_type_suggestions table
    op.create_table(
        'business_type_suggestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_type', sa.String(length=50), nullable=False),
        sa.Column('keywords', postgresql.JSON(), nullable=True),
        sa.Column('phrases', postgresql.JSON(), nullable=True),
        sa.Column('confidence_weight', sa.Numeric(precision=3, scale=2), nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_type_suggestions_id'), 'business_type_suggestions', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_business_type_suggestions_id'), table_name='business_type_suggestions')
    op.drop_table('business_type_suggestions')
    
    op.drop_index(op.f('ix_intent_classifications_id'), table_name='intent_classifications')
    op.drop_table('intent_classifications')
    
    op.drop_index(op.f('ix_template_versions_id'), table_name='template_versions')
    op.drop_table('template_versions')
    
    op.drop_index(op.f('ix_business_templates_template_key'), table_name='business_templates')
    op.drop_index(op.f('ix_business_templates_id'), table_name='business_templates')
    op.drop_table('business_templates')