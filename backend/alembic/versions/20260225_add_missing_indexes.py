"""add_missing_indexes

Revision ID: f1a2b3c4d5e6
Revises: d88db6c8283c
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'd88db6c8283c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Foreign key indexes
    op.create_index('ix_call_sessions_customer_id', 'call_sessions', ['customer_id'])
    op.create_index('ix_system_logs_user_id', 'system_logs', ['user_id'])
    op.create_index('ix_system_logs_business_id', 'system_logs', ['business_id'])
    op.create_index('ix_ai_training_scenarios_business_id', 'ai_training_scenarios', ['business_id'])
    op.create_index('ix_appointments_business_id', 'appointments', ['business_id'])
    op.create_index('ix_appointments_customer_id', 'appointments', ['customer_id'])
    op.create_index('ix_menu_items_business_id', 'menu_items', ['business_id'])
    op.create_index('ix_orders_business_id', 'orders', ['business_id'])
    op.create_index('ix_orders_customer_id', 'orders', ['customer_id'])
    op.create_index('ix_orders_call_session_id', 'orders', ['call_session_id'])
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_menu_item_id', 'order_items', ['menu_item_id'])
    op.create_index('ix_knowledge_base_documents_business_id', 'knowledge_base_documents', ['business_id'])
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_approval_requests_business_id', 'approval_requests', ['business_id'])
    op.create_index('ix_approval_requests_call_session_id', 'approval_requests', ['call_session_id'])
    op.create_index('ix_approval_requests_reviewed_by', 'approval_requests', ['reviewed_by'])
    op.create_index('ix_manager_actions_approval_request_id', 'manager_actions', ['approval_request_id'])
    op.create_index('ix_manager_actions_manager_id', 'manager_actions', ['manager_id'])
    op.create_index('ix_webhooks_business_id', 'webhooks', ['business_id'])
    op.create_index('ix_calendar_integrations_business_id', 'calendar_integrations', ['business_id'])
    op.create_index('ix_sms_templates_business_id', 'sms_templates', ['business_id'])
    op.create_index('ix_template_versions_template_id', 'template_versions', ['template_id'])
    op.create_index('ix_customers_business_id', 'customers', ['business_id'])
    op.create_index('ix_call_recordings_call_session_id', 'call_recordings', ['call_session_id'])
    op.create_index('ix_call_recordings_business_id', 'call_recordings', ['business_id'])
    op.create_index('ix_team_members_business_id', 'team_members', ['business_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])

    # Scheduling-critical
    op.create_index('ix_appointments_appointment_time', 'appointments', ['appointment_time'])

    # Compound indexes for dashboard queries
    op.create_index('ix_appointments_biz_time', 'appointments', ['business_id', 'appointment_time'])
    op.create_index('ix_orders_biz_status', 'orders', ['business_id', 'status'])
    op.create_index('ix_customers_biz_phone', 'customers', ['business_id', 'phone'])
    op.create_index('ix_call_sessions_biz_started', 'call_sessions', ['business_id', 'started_at'])
    op.create_index('ix_approval_requests_biz_status', 'approval_requests', ['business_id', 'status'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    # Compound indexes
    op.drop_index('ix_audit_logs_created_at', 'audit_logs')
    op.drop_index('ix_approval_requests_biz_status', 'approval_requests')
    op.drop_index('ix_call_sessions_biz_started', 'call_sessions')
    op.drop_index('ix_customers_biz_phone', 'customers')
    op.drop_index('ix_orders_biz_status', 'orders')
    op.drop_index('ix_appointments_biz_time', 'appointments')

    # Scheduling-critical
    op.drop_index('ix_appointments_appointment_time', 'appointments')

    # Foreign key indexes
    op.drop_index('ix_team_members_user_id', 'team_members')
    op.drop_index('ix_team_members_business_id', 'team_members')
    op.drop_index('ix_call_recordings_business_id', 'call_recordings')
    op.drop_index('ix_call_recordings_call_session_id', 'call_recordings')
    op.drop_index('ix_customers_business_id', 'customers')
    op.drop_index('ix_template_versions_template_id', 'template_versions')
    op.drop_index('ix_sms_templates_business_id', 'sms_templates')
    op.drop_index('ix_calendar_integrations_business_id', 'calendar_integrations')
    op.drop_index('ix_webhooks_business_id', 'webhooks')
    op.drop_index('ix_manager_actions_manager_id', 'manager_actions')
    op.drop_index('ix_manager_actions_approval_request_id', 'manager_actions')
    op.drop_index('ix_approval_requests_reviewed_by', 'approval_requests')
    op.drop_index('ix_approval_requests_call_session_id', 'approval_requests')
    op.drop_index('ix_approval_requests_business_id', 'approval_requests')
    op.drop_index('ix_document_chunks_document_id', 'document_chunks')
    op.drop_index('ix_knowledge_base_documents_business_id', 'knowledge_base_documents')
    op.drop_index('ix_order_items_menu_item_id', 'order_items')
    op.drop_index('ix_order_items_order_id', 'order_items')
    op.drop_index('ix_orders_call_session_id', 'orders')
    op.drop_index('ix_orders_customer_id', 'orders')
    op.drop_index('ix_orders_business_id', 'orders')
    op.drop_index('ix_menu_items_business_id', 'menu_items')
    op.drop_index('ix_appointments_customer_id', 'appointments')
    op.drop_index('ix_appointments_business_id', 'appointments')
    op.drop_index('ix_ai_training_scenarios_business_id', 'ai_training_scenarios')
    op.drop_index('ix_system_logs_business_id', 'system_logs')
    op.drop_index('ix_system_logs_user_id', 'system_logs')
    op.drop_index('ix_call_sessions_customer_id', 'call_sessions')
