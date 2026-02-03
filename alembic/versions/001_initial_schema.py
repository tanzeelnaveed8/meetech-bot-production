"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE state AS ENUM (
            'GREETING', 'INTENT_DETECTION', 'QUALIFICATION', 'SCORING',
            'PROOF_DELIVERY', 'CALL_PUSH', 'HUMAN_HANDOVER', 'FOLLOW_UP',
            'EXIT', 'PARK'
        )
    """)

    op.execute("""
        CREATE TYPE sender AS ENUM ('LEAD', 'BOT', 'HUMAN')
    """)

    op.execute("""
        CREATE TYPE messagetype AS ENUM (
            'TEXT', 'IMAGE', 'VOICE', 'DOCUMENT', 'BUTTON_REPLY'
        )
    """)

    op.execute("""
        CREATE TYPE scorecategory AS ENUM ('LOW', 'MEDIUM', 'HIGH')
    """)

    op.execute("""
        CREATE TYPE assettype AS ENUM ('PORTFOLIO', 'CASE_STUDY', 'TESTIMONIAL')
    """)

    op.execute("""
        CREATE TYPE followupscenario AS ENUM (
            'INACTIVE', 'CALL_NOT_BOOKED', 'CALL_MISSED', 'PROPOSAL_SENT'
        )
    """)

    # Create human_agents table
    op.create_table(
        'human_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_concurrent_conversations', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_human_agents_email', 'human_agents', ['email'])
    op.create_index('ix_human_agents_is_available', 'human_agents', ['is_available'])

    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('phone_number', sa.String(20), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('project_type', sa.String(100), nullable=True),
        sa.Column('budget', sa.String(100), nullable=True),
        sa.Column('budget_numeric', sa.Integer(), nullable=True),
        sa.Column('timeline', sa.String(100), nullable=True),
        sa.Column('business_type', sa.String(100), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('current_state', postgresql.ENUM(name='state'), nullable=False, server_default='GREETING'),
        sa.Column('budget_avoidance_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assigned_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_agent_id'], ['human_agents.id']),
    )
    op.create_index('ix_leads_phone_number', 'leads', ['phone_number'])
    op.create_index('ix_leads_created_at', 'leads', ['created_at'])
    op.create_index('ix_leads_current_state', 'leads', ['current_state'])
    op.create_index('ix_leads_assigned_agent_id', 'leads', ['assigned_agent_id'])

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('current_state', postgresql.ENUM(name='state'), nullable=False, server_default='GREETING'),
        sa.Column('previous_state', postgresql.ENUM(name='state'), nullable=True),
        sa.Column('is_bot_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('human_takeover_at', sa.DateTime(), nullable=True),
        sa.Column('human_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('proof_asset_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_conversations_lead_id', 'conversations', ['lead_id'])
    op.create_index('ix_conversations_started_at', 'conversations', ['started_at'])
    op.create_index('ix_conversations_current_state', 'conversations', ['current_state'])
    op.create_index('ix_conversations_is_bot_active', 'conversations', ['is_bot_active'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender', postgresql.ENUM(name='sender'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('message_type', postgresql.ENUM(name='messagetype'), nullable=False, server_default='TEXT'),
        sa.Column('detected_intent', sa.String(100), nullable=True),
        sa.Column('intent_confidence', sa.Float(), nullable=True),
        sa.Column('whatsapp_message_id', sa.String(255), nullable=True, unique=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_timestamp', 'messages', ['timestamp'])
    op.create_index('ix_messages_whatsapp_message_id', 'messages', ['whatsapp_message_id'])

    # Create lead_scores table
    op.create_table(
        'lead_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('budget_score', sa.Integer(), nullable=False),
        sa.Column('timeline_score', sa.Integer(), nullable=False),
        sa.Column('clarity_score', sa.Integer(), nullable=False),
        sa.Column('country_score', sa.Integer(), nullable=False),
        sa.Column('behavior_score', sa.Integer(), nullable=False),
        sa.Column('score_category', postgresql.ENUM(name='scorecategory'), nullable=False),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('triggered_handover', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_lead_scores_lead_id', 'lead_scores', ['lead_id'])
    op.create_index('ix_lead_scores_calculated_at', 'lead_scores', ['calculated_at'])
    op.create_index('ix_lead_scores_score_category', 'lead_scores', ['score_category'])
    op.create_index('ix_lead_scores_triggered_handover', 'lead_scores', ['triggered_handover'])

    # Create state_transitions table
    op.create_table(
        'state_transitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_state', postgresql.ENUM(name='state'), nullable=False),
        sa.Column('to_state', postgresql.ENUM(name='state'), nullable=False),
        sa.Column('transitioned_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('trigger', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_state_transitions_conversation_id', 'state_transitions', ['conversation_id'])
    op.create_index('ix_state_transitions_transitioned_at', 'state_transitions', ['transitioned_at'])
    op.create_index('ix_state_transitions_from_state', 'state_transitions', ['from_state'])
    op.create_index('ix_state_transitions_to_state', 'state_transitions', ['to_state'])

    # Create proof_assets table
    op.create_table(
        'proof_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('asset_type', postgresql.ENUM(name='assettype'), nullable=False),
        sa.Column('project_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_proof_assets_asset_type', 'proof_assets', ['asset_type'])
    op.create_index('ix_proof_assets_project_type', 'proof_assets', ['project_type'])
    op.create_index('ix_proof_assets_is_active', 'proof_assets', ['is_active'])

    # Create follow_ups table
    op.create_table(
        'follow_ups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_scenario', postgresql.ENUM(name='followupscenario'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('lead_responded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('response_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('message_content', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_follow_ups_lead_id', 'follow_ups', ['lead_id'])
    op.create_index('ix_follow_ups_trigger_scenario', 'follow_ups', ['trigger_scenario'])
    op.create_index('ix_follow_ups_scheduled_at', 'follow_ups', ['scheduled_at'])
    op.create_index('ix_follow_ups_sent_at', 'follow_ups', ['sent_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('follow_ups')
    op.drop_table('proof_assets')
    op.drop_table('state_transitions')
    op.drop_table('lead_scores')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('leads')
    op.drop_table('human_agents')

    # Drop enum types
    op.execute('DROP TYPE followupscenario')
    op.execute('DROP TYPE assettype')
    op.execute('DROP TYPE scorecategory')
    op.execute('DROP TYPE messagetype')
    op.execute('DROP TYPE sender')
    op.execute('DROP TYPE state')
