"""add teacher_annotations to submissions

Free-form teacher annotations (highlights, inline corrections and comments) on the student's
text, stored as a JSON list. Nullable with no default: an existing submission simply has no
annotations, which the model reads as an empty list.

Revision ID: 7c1e4b9f2d38
Revises: 352b04c9e747
Create Date: 2026-09-28
"""
from alembic import op
import sqlalchemy as sa

revision = '7c1e4b9f2d38'
down_revision = '352b04c9e747'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('submissions', sa.Column('teacher_annotations', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('submissions', 'teacher_annotations')
