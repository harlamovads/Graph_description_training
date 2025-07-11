# models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Configure naming convention for constraints
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

from backend.models.user import User, Invitation
from backend.models.task import Task, TaskAssignment
from backend.models.submission import Submission
from backend.models.exercise import Exercise, ExerciseAttempt
from backend.models.sentence import Sentence

def init_app(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)