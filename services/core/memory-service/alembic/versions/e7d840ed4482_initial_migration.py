"""initial migration

Revision ID: e7d840ed4482
Revises: 
Create Date: 2026-06-06 20:35:51.651749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TEXT

# revision identifiers, used by Alembic.
revision: str = 'e7d840ed4482'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sessions table first
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create messages table with foreign key to sessions
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', TEXT, nullable=False),
        sa.Column('token_count', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Add indexes and constraints after tables are created
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('ix_messages_session_id', 'messages', ['session_id'])
    op.create_foreign_key('fk_messages_session_id', 'messages', 'sessions', ['session_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('uq_messages_id', 'messages', ['id'])
    op.create_unique_constraint('uq_sessions_id', 'sessions', ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_constraint('uq_sessions_id', 'sessions', type_='unique')
    op.drop_constraint('uq_messages_id', 'messages', type_='unique')
    op.drop_constraint('fk_messages_session_id', 'messages', type_='foreignkey')
    op.drop_index('ix_messages_session_id', table_name='messages')
    op.drop_index('ix_sessions_user_id', table_name='sessions')
    op.drop_table('messages')
    op.drop_table('sessions')