"""initial schema

Genesis migration, inserted after the fact. The two migrations that originally started this
chain (9d93b537b5dc, f42d3069a5b8) were written as incremental ALTERs on top of a base schema
that was always created by db.create_all() at runtime (see the old init_db.py), never by a
migration - so `flask db upgrade` on a genuinely empty database had no way to create `users`,
`tasks`, `submissions`, etc. in the first place. This migration recreates that base schema
exactly as it looked at that point in history (including the since-removed
exercises/exercise_attempts/sentences tables, dropped later by
12a40c90d01c_replace_exercise_system_with_practice_.py), using unnamed default constraints to
match what db.create_all() actually produced - so this chain applies cleanly both to a fresh
database and to one that already has this schema from create_all() (via `flask db stamp`,
see README).

Revision ID: 0a1b2c3d4e5f
Revises:
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa

revision = '0a1b2c3d4e5f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=64), nullable=False, unique=True),
        sa.Column('email', sa.String(length=120), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=512)),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=255), nullable=False),
        sa.Column('is_from_database', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'task_assignments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('due_date', sa.DateTime()),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'invitations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=20), nullable=False, unique=True),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'exercises',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source_submission_id', sa.Integer()),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('sentences', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=255)),
        sa.Column('status', sa.String(length=20), server_default='draft'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'sentences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('error_tags', sa.Text()),
    )
    op.create_table(
        'exercise_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('responses', sa.Text()),
        sa.Column('analysis_result', sa.Text()),
        sa.Column('score', sa.Float()),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('task_assignments.id'), nullable=False),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id')),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('analysis_result', sa.Text()),
        sa.Column('teacher_feedback', sa.Text()),
        sa.Column('status', sa.String(length=20), server_default='submitted'),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('reviewed_at', sa.DateTime()),
        sa.Column('analysis_html', sa.Text()),
    )


def downgrade():
    op.drop_table('submissions')
    op.drop_table('exercise_attempts')
    op.drop_table('sentences')
    op.drop_table('exercises')
    op.drop_table('invitations')
    op.drop_table('task_assignments')
    op.drop_table('tasks')
    op.drop_table('users')
