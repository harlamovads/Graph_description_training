"""allow practice sessions that came from a student's own sentence

A practice session used to require a submission to have come from. A student can now type a
sentence themselves, mark the errors in it and practise that, so both columns become nullable.
Nothing else changes: such a session runs through exactly the same rounds.

Revision ID: c94d7e2a5b11
Revises: b83f5a1c7e64
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa

revision = 'c94d7e2a5b11'
down_revision = 'b83f5a1c7e64'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('practice_sessions', 'submission_id',
                    existing_type=sa.Integer(), nullable=True)
    op.alter_column('practice_sessions', 'sentence_index',
                    existing_type=sa.Integer(), nullable=True)


def downgrade():
    # Manual sessions have no submission to point at, so they cannot survive the column
    # becoming NOT NULL again. Remove them (and any practice assignment referencing them)
    # rather than letting the ALTER fail on a populated database.
    op.execute("""
        UPDATE practice_assignments SET practice_session_id = NULL
        WHERE practice_session_id IN (
            SELECT id FROM practice_sessions WHERE submission_id IS NULL
        )
    """)
    op.execute("DELETE FROM error_logs WHERE source_type = 'practice_session' AND source_id IN "
               "(SELECT id FROM practice_sessions WHERE submission_id IS NULL)")
    op.execute("DELETE FROM practice_sessions WHERE submission_id IS NULL")
    op.alter_column('practice_sessions', 'sentence_index',
                    existing_type=sa.Integer(), nullable=False)
    op.alter_column('practice_sessions', 'submission_id',
                    existing_type=sa.Integer(), nullable=False)
