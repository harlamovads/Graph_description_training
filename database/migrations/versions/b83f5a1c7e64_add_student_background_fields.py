"""add student background fields to users

Age, gender, native language and English level, filled in by a student from their profile page.
All nullable: they are optional, and every existing account predates them.

Revision ID: b83f5a1c7e64
Revises: 7c1e4b9f2d38
Create Date: 2026-09-28
"""
from alembic import op
import sqlalchemy as sa

revision = 'b83f5a1c7e64'
down_revision = '7c1e4b9f2d38'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('gender', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('native_language', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('english_level', sa.String(length=32), nullable=True))


def downgrade():
    op.drop_column('users', 'english_level')
    op.drop_column('users', 'native_language')
    op.drop_column('users', 'gender')
    op.drop_column('users', 'age')
