"""initial enterprise schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-11-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Named ENUM definitions
ticket_status_enum = sa.Enum('Open', 'In Progress', 'Resolved', 'Closed', name='ticketstatusenum')
ai_review_status_enum = sa.Enum('Pending', 'Approved', 'Rejected', 'Not Required', 'Failed', name='aireviewstatusenum')
priority_enum = sa.Enum('Low', 'Medium', 'High', 'Critical', name='priorityenum')


def upgrade() -> None:
    # 1. Create 'tickets' table
    op.create_table(
        'tickets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ticket_status', ticket_status_enum, nullable=False, server_default='Open'),
        sa.Column('ai_review_status', ai_review_status_enum, nullable=False, server_default='Not Required'),
        sa.Column('priority', priority_enum, nullable=False, server_default='Medium'),
        sa.Column('ai_triage_category', sa.String(length=100), nullable=True),
        sa.Column('ai_drafted_response', sa.Text(), nullable=True),
        sa.Column('ai_citations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tickets'))
    )

    op.create_index(op.f('ix_tickets_title'), 'tickets', ['title'], unique=False)
    op.create_index(op.f('ix_tickets_ticket_status'), 'tickets', ['ticket_status'], unique=False)
    op.create_index(op.f('ix_tickets_ai_review_status'), 'tickets', ['ai_review_status'], unique=False)
    op.create_index(op.f('ix_tickets_priority'), 'tickets', ['priority'], unique=False)
    op.create_index(op.f('ix_tickets_ai_triage_category'), 'tickets', ['ai_triage_category'], unique=False)
    op.create_index(op.f('ix_tickets_status_priority'), 'tickets', ['ticket_status', 'priority'], unique=False)

    # 2. Create 'ticket_history' table
    op.create_table(
        'ticket_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('ticket_id', sa.String(length=36), nullable=False),
        sa.Column('previous_state', sa.JSON(), nullable=False),
        sa.Column('new_state', sa.JSON(), nullable=False),
        sa.Column('changed_by', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ['ticket_id'],
            ['tickets.id'],
            name=op.f('fk_ticket_history_ticket_id_tickets'),
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ticket_history'))
    )

    op.create_index(op.f('ix_ticket_history_ticket_id'), 'ticket_history', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_ticket_history_timestamp'), 'ticket_history', ['timestamp'], unique=False)


def downgrade() -> None:
    # 1. Drop 'ticket_history' and indexes
    op.drop_index(op.f('ix_ticket_history_timestamp'), table_name='ticket_history')
    op.drop_index(op.f('ix_ticket_history_ticket_id'), table_name='ticket_history')
    op.drop_table('ticket_history')

    # 2. Drop 'tickets' and indexes
    op.drop_index(op.f('ix_tickets_status_priority'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_ai_triage_category'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_priority'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_ai_review_status'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_ticket_status'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_title'), table_name='tickets')
    op.drop_table('tickets')

    # 3. Clean up PostgreSQL ENUM types if running on PostgreSQL dialect
    bind = op.get_bind()
    if bind and bind.dialect.name == 'postgresql':
        priority_enum.drop(bind, checkfirst=True)
        ai_review_status_enum.drop(bind, checkfirst=True)
        ticket_status_enum.drop(bind, checkfirst=True)
