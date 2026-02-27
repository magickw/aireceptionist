"""add_language_to_businesses

Revision ID: 20260227_lang
Revises: b2c3d4e5f6a7
Create Date: 2026-02-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260227_lang'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add language column to businesses
    op.add_column('businesses', sa.Column('language', sa.String(length=10), server_default='en-US', nullable=True))
    
    # Add translated_content column to conversation_messages (from my previous model change)
    op.add_column('conversation_messages', sa.Column('translated_content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('conversation_messages', 'translated_content')
    op.drop_column('businesses', 'language')
